import datetime
from zoneinfo import ZoneInfo

from app.application.availability import calculate_free_slots
from app.domain.models.plantilla import PlantillaDisponibilidad

DEFAULT_CLINIC_TIMEZONE = "America/Argentina/Buenos_Aires"


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
