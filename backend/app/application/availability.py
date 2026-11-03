import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import EstadoTurno
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.infrastructure.config import get_settings


class SlotDisponible(BaseModel):
    """Pydantic model representing an available appointment time slot.
    
    Hard Rule #1: extra='forbid' to reject undeclared fields.
    """
    model_config = ConfigDict(extra="forbid")

    inicio: datetime.datetime
    fin: datetime.datetime
    odontologo_id: int
    prestacion: str


def _normalize_dt(dt: datetime.datetime, zone: ZoneInfo) -> datetime.datetime:
    """Ensures datetime is timezone-aware in the target clinic timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=zone)
    return dt.astimezone(zone)


def calculate_free_slots(
    fecha: datetime.date,
    templates: list[PlantillaDisponibilidad],
    turnos: list[Turno],
    timezone_str: str | None = None,
    now_override: datetime.datetime | None = None,
) -> list[SlotDisponible]:
    """Pure synchronous helper for partitioning availability templates into free slots.
    
    Strictly adheres to:
    - Hard Rule #3: pure synchronous def function with zero async I/O.
    - RN-AG-01 & RN-AG-02: dynamic derivation from templates without empty DB rows.
    - RN-GL-02: rejects past dates and omits elapsed slots when fecha == today.
    - CB-02: disallows incomplete remainder slots (slot_inicio + duracion <= template_fin).
    - CB-03 & RN-TU-04: appointments in 'cancelado' or 'anulado' release their slot.
    - CB-04: appointments straddling slots block all intersected slots.
    - CB-05: omits slots whose start time has already passed on current clinic day.
    """
    if timezone_str:
        tz_name = timezone_str
    else:
        try:
            tz_name = get_settings().TIMEZONE
        except Exception:
            tz_name = "America/Argentina/Buenos_Aires"
    zone = ZoneInfo(tz_name)

    if now_override is not None:
        now_local = _normalize_dt(now_override, zone)
    else:
        now_local = datetime.datetime.now(zone)

    today_local = now_local.date()
    if fecha < today_local:
        raise ValueError("No se puede consultar disponibilidad para fechas pasadas.")

    # Filter out cancelled or annulled appointments (CB-03, RN-TU-04)
    active_turnos: list[Turno] = []
    inactive_states = {EstadoTurno.CANCELADO, EstadoTurno.ANULADO}
    for t in turnos:
        # Check both enum instance and string/value representation
        if t.estado not in inactive_states and str(t.estado.value).lower() not in {"cancelado", "anulado"}:
            active_turnos.append(t)

    # Filter templates matching day of the week (0 = Monday, 6 = Sunday)
    dia_semana = fecha.weekday()
    matching_templates = [
        tpl for tpl in templates if tpl.dia_semana == dia_semana
    ]
    matching_templates.sort(key=lambda tpl: tpl.hora_inicio)

    free_slots: list[SlotDisponible] = []

    for template in matching_templates:
        template_inicio = datetime.datetime.combine(fecha, template.hora_inicio, tzinfo=zone)
        template_fin = datetime.datetime.combine(fecha, template.hora_fin, tzinfo=zone)
        slot_duration = datetime.timedelta(minutes=template.duracion_slot_minutos)

        slot_inicio = template_inicio
        # CB-02: Only complete slots ending before or at template_fin
        while slot_inicio + slot_duration <= template_fin:
            slot_fin = slot_inicio + slot_duration

            # CB-05: If fecha is today, omit slots whose start time has already passed
            if fecha == today_local and slot_inicio <= now_local:
                slot_inicio = slot_fin
                continue

            # CB-04 & RN-AG-01: Check overlap with active appointments
            # Overlap predicate: turno.inicio < slot_fin AND turno.fin > slot_inicio
            has_conflict = False
            for turno in active_turnos:
                t_inicio = _normalize_dt(turno.inicio, zone)
                t_fin = _normalize_dt(turno.fin, zone)
                if t_inicio < slot_fin and t_fin > slot_inicio:
                    has_conflict = True
                    break

            if not has_conflict:
                free_slots.append(
                    SlotDisponible(
                        inicio=slot_inicio,
                        fin=slot_fin,
                        odontologo_id=template.odontologo_id,
                        prestacion=template.prestacion,
                    )
                )

            slot_inicio = slot_fin

    return free_slots
