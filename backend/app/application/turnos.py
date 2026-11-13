import datetime
from zoneinfo import ZoneInfo

from app.application.availability import calculate_free_slots
from app.domain.models.enums import EstadoTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno

DEFAULT_CLINIC_TIMEZONE = "America/Argentina/Buenos_Aires"
DEFAULT_CANCEL_MIN_HOURS = 24


class UnauthorizedTransitionError(Exception):
    """Raised when a user's role or resource ownership forbids the requested state transition (HTTP 403)."""


class InvalidStateTransitionError(Exception):
    """Raised when the appointment's current state does not allow transitioning to the target state (HTTP 409)."""


class AnticipationWindowError(Exception):
    """Raised when a cancellation/annulment violates CANCEL_MIN_HOURS or confirmation is in the past (HTTP 422)."""


_ROLE_ALLOWED_TARGETS: dict[RolUsuario, frozenset[EstadoTurno]] = {
    RolUsuario.PACIENTE: frozenset({EstadoTurno.CANCELADO}),
    RolUsuario.RECEPCION: frozenset({EstadoTurno.CONFIRMADO, EstadoTurno.ANULADO}),
    RolUsuario.ODONTOLOGO: frozenset({EstadoTurno.PRESENTE, EstadoTurno.AUSENTE}),
}

_VALID_SOURCE_STATES: dict[EstadoTurno, frozenset[EstadoTurno]] = {
    EstadoTurno.CONFIRMADO: frozenset({EstadoTurno.SOLICITADO}),
    EstadoTurno.CANCELADO: frozenset({EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO}),
    EstadoTurno.ANULADO: frozenset({EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO}),
    EstadoTurno.PRESENTE: frozenset({EstadoTurno.CONFIRMADO}),
    EstadoTurno.AUSENTE: frozenset({EstadoTurno.CONFIRMADO}),
}


def _normalize_dt(dt: datetime.datetime, zone: ZoneInfo) -> datetime.datetime:
    """Ensures a datetime is timezone-aware in the clinic timezone."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=zone)
    return dt.astimezone(zone)


def validate_slot_matches_template(
    inicio: datetime.datetime,
    fin: datetime.datetime,
    templates: list[PlantillaDisponibilidad],
    timezone_str: str | None = None,
    now_override: datetime.datetime | None = None,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Pure synchronous validator verifying that [inicio, fin) is in the future and matches an exact template slot.

    Strictly adheres to:
    - Hard Rule #3 & Clean Architecture: pure synchronous def function with zero I/O or infrastructure imports.
    - RN-GL-02 & CB-05: rejects past dates and already elapsed slots on the current clinic day.
    - RN-AG-02 & CB-02: requires exact alignment with a complete slot of duracion_slot_minutos.
    """
    tz_name = timezone_str or DEFAULT_CLINIC_TIMEZONE
    zone = ZoneInfo(tz_name)

    inicio_local = _normalize_dt(inicio, zone)
    fin_local = _normalize_dt(fin, zone)

    if fin_local <= inicio_local:
        raise ValueError("El horario de fin debe ser estrictamente posterior al horario de inicio.")

    if inicio_local.date() != fin_local.date():
        raise ValueError("RN-AG-02: El turno solicitado debe comenzar y finalizar en la misma fecha del consultorio.")

    if now_override is not None:
        now_local = _normalize_dt(now_override, zone)
    else:
        now_local = datetime.datetime.now(zone)

    if inicio_local.date() < now_local.date():
        raise ValueError("RN-GL-02: No se pueden solicitar turnos en fechas pasadas.")

    if inicio_local <= now_local:
        raise ValueError("RN-GL-02: El horario solicitado ya ha transcurrido en la fecha actual.")

    # Derive valid template grid slots for that date (turnos=[] checks pure template alignment + CB-02 + CB-05)
    valid_template_slots = calculate_free_slots(
        fecha=inicio_local.date(),
        templates=templates,
        turnos=[],
        timezone_str=tz_name,
        now_override=now_local,
    )

    for slot in valid_template_slots:
        if slot.inicio == inicio_local and slot.fin == fin_local:
            return inicio_local, fin_local

    raise ValueError(
        "RN-AG-02: El intervalo solicitado no coincide con un slot válido de la plantilla del odontólogo."
    )


def validate_state_transition(
    actor_rol: RolUsuario,
    actor_user_id: int,
    turno_paciente_id: int,
    turno_odontologo_id: int,
    estado_actual: EstadoTurno,
    nuevo_estado: EstadoTurno,
    turno_inicio: datetime.datetime,
    now_local: datetime.datetime,
    cancel_min_hours: int = DEFAULT_CANCEL_MIN_HOURS,
    timezone_str: str | None = None,
) -> None:
    """Pure synchronous appointment state-machine and anticipation validator.

    Strictly adheres to:
    - Hard Rule #3 & Clean Architecture: 100% pure synchronous def function with zero I/O,
      zero system-clock calls, and zero infrastructure imports.
    - Defense-in-depth evaluation order:
      1. Role-to-target-state allowlist (RN-TU-01..04, RN-GL-01) -> UnauthorizedTransitionError (403)
      2. Resource ownership (RN-AU-02, RN-GL-01, OWASP BOLA) -> UnauthorizedTransitionError (403)
      3. Source-to-target state matrix (DD-03, US-004, US-006, US-008) -> InvalidStateTransitionError (409)
      4. Minimum anticipation & future check (RN-TU-05, RN-GL-02) -> AnticipationWindowError (422)
    """
    allowed_targets = _ROLE_ALLOWED_TARGETS.get(actor_rol, frozenset())
    if nuevo_estado not in allowed_targets:
        raise UnauthorizedTransitionError(
            f"RN-GL-01: El rol '{actor_rol.value}' no tiene permiso para transicionar un turno al estado '{nuevo_estado.value}'."
        )

    if actor_rol == RolUsuario.PACIENTE and turno_paciente_id != actor_user_id:
        raise UnauthorizedTransitionError(
            "RN-GL-01: El paciente solo puede cancelar sus propios turnos."
        )

    if actor_rol == RolUsuario.ODONTOLOGO and turno_odontologo_id != actor_user_id:
        raise UnauthorizedTransitionError(
            "RN-AU-02: El odontólogo solo puede registrar asistencia sobre sus propios turnos asignados."
        )

    valid_sources = _VALID_SOURCE_STATES.get(nuevo_estado, frozenset())
    if estado_actual not in valid_sources:
        raise InvalidStateTransitionError(
            f"Transición de estado inválida: no se puede pasar de '{estado_actual.value}' a '{nuevo_estado.value}'."
        )

    tz_name = timezone_str or DEFAULT_CLINIC_TIMEZONE
    zone = ZoneInfo(tz_name)
    inicio_norm = _normalize_dt(turno_inicio, zone)
    now_norm = _normalize_dt(now_local, zone)

    if nuevo_estado in (EstadoTurno.CANCELADO, EstadoTurno.ANULADO):
        min_delta = datetime.timedelta(hours=cancel_min_hours)
        if inicio_norm - now_norm < min_delta:
            raise AnticipationWindowError(
                f"RN-TU-05: La cancelación o anulación requiere al menos {cancel_min_hours} horas de anticipación."
            )
    elif nuevo_estado == EstadoTurno.CONFIRMADO:
        if inicio_norm <= now_norm:
            raise AnticipationWindowError(
                "RN-GL-02: No se puede confirmar un turno cuya fecha u hora de inicio ya ha transcurrido."
            )


def get_clinic_day_bounds(
    fecha: datetime.date,
    timezone_str: str | None = None,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Pure synchronous helper computing the half-open clinic day interval [00:00:00, +1 day 00:00:00).

    Strictly adheres to Hard Rule #3: synchronous def with zero I/O or infrastructure imports.
    """
    tz_name = timezone_str or DEFAULT_CLINIC_TIMEZONE
    zone = ZoneInfo(tz_name)
    day_start = datetime.datetime.combine(fecha, datetime.time.min, tzinfo=zone)
    day_end = day_start + datetime.timedelta(days=1)
    return day_start, day_end


def get_clinic_date_range_bounds(
    fecha_desde: datetime.date | None = None,
    fecha_hasta: datetime.date | None = None,
    timezone_str: str | None = None,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Pure synchronous helper computing the inclusive clinic date range [start, end) in clinic timezone.

    Strictly adheres to Hard Rule #3: synchronous def with zero I/O, zero system clock calls,
    and zero infrastructure imports.
    """
    if fecha_desde is not None and fecha_hasta is not None and fecha_hasta < fecha_desde:
        raise ValueError("fecha_hasta debe ser mayor o igual a fecha_desde.")

    tz_name = timezone_str or DEFAULT_CLINIC_TIMEZONE
    zone = ZoneInfo(tz_name)
    start_date = fecha_desde or datetime.date(1970, 1, 1)
    end_date = fecha_hasta or datetime.date(2100, 1, 1)

    range_start = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=zone)
    range_end = datetime.datetime.combine(end_date, datetime.time.min, tzinfo=zone) + datetime.timedelta(days=1)
    return range_start, range_end


def get_clinic_month_bounds(
    anio: int,
    mes: int,
    timezone_str: str | None = None,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Return half-open [month_start, next_month_start) bounds in the clinic timezone."""
    if mes < 1 or mes > 12:
        raise ValueError("El mes debe estar entre 1 y 12.")

    zone = ZoneInfo(timezone_str or DEFAULT_CLINIC_TIMEZONE)
    month_start = datetime.datetime(anio, mes, 1, 0, 0, 0, tzinfo=zone)
    if mes == 12:
        next_month_start = datetime.datetime(anio + 1, 1, 1, 0, 0, 0, tzinfo=zone)
    else:
        next_month_start = datetime.datetime(anio, mes + 1, 1, 0, 0, 0, tzinfo=zone)
    return month_start, next_month_start


def summarize_dentist_month_appointments(
    turnos: list[Turno],
    anio: int,
    mes: int,
    timezone_str: str | None = None,
) -> list[dict[str, int | datetime.date]]:
    """Aggregate active dentist appointments by local clinic date, excluding cancelled/annulled."""
    zone = ZoneInfo(timezone_str or DEFAULT_CLINIC_TIMEZONE)
    counts_by_date: dict[datetime.date, dict[str, int]] = {}

    for turno in turnos:
        estado = EstadoTurno(turno.estado)
        if estado in (EstadoTurno.CANCELADO, EstadoTurno.ANULADO):
            continue

        inicio_dt = _normalize_dt(turno.inicio, zone).astimezone(zone)
        local_date = inicio_dt.date()
        if local_date.year != anio or local_date.month != mes:
            continue

        bucket = counts_by_date.setdefault(
            local_date,
            {"confirmados": 0, "solicitados": 0, "atendidos": 0},
        )
        if estado == EstadoTurno.CONFIRMADO:
            bucket["confirmados"] += 1
        elif estado == EstadoTurno.SOLICITADO:
            bucket["solicitados"] += 1
        elif estado in (EstadoTurno.PRESENTE, EstadoTurno.AUSENTE):
            bucket["atendidos"] += 1

    return [
        {
            "fecha": fecha,
            "confirmados": bucket["confirmados"],
            "solicitados": bucket["solicitados"],
            "atendidos": bucket["atendidos"],
            "total_activos": bucket["confirmados"] + bucket["solicitados"] + bucket["atendidos"],
        }
        for fecha, bucket in sorted(counts_by_date.items())
    ]




