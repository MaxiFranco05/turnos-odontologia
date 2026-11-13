import calendar
import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.turnos import DEFAULT_CLINIC_TIMEZONE, _normalize_dt
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario

DEMO_DENTIST_EMAILS = (
    "sofia.martin@turnosodontologia.com",
    "lucas.garcia@turnosodontologia.com",
)
DEMO_PATIENT_EMAILS = (
    "carlos.benitez@example.com",
    "lucia.gomez@example.com",
)


def _select_month_weekdays(reference_date: datetime.date, count: int = 4) -> list[datetime.date]:
    """Select up to `count` weekdays in reference_date's month, preferring >= reference_date."""
    _, days_in_month = calendar.monthrange(reference_date.year, reference_date.month)
    month_weekdays = [
        datetime.date(reference_date.year, reference_date.month, day)
        for day in range(1, days_in_month + 1)
        if datetime.date(reference_date.year, reference_date.month, day).weekday() < 5
    ]
    upcoming = [d for d in month_weekdays if d >= reference_date]
    if len(upcoming) >= count:
        return upcoming[:count]

    earlier = [d for d in month_weekdays if d < reference_date]
    needed = count - len(upcoming)
    selected = sorted(upcoming + earlier[-needed:])
    return selected


def _iter_day_slots(
    templates: list[PlantillaDisponibilidad],
    target_day: datetime.date,
    preferred_time: datetime.time,
    zone: ZoneInfo,
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """Yield candidate 30-min slots on target_day starting from preferred_time, ordered cleanly."""
    candidates: list[tuple[datetime.datetime, datetime.datetime]] = []
    weekday = target_day.weekday()
    for tpl in sorted(templates, key=lambda p: p.hora_inicio):
        if tpl.dia_semana != weekday:
            continue
        cursor = datetime.datetime.combine(target_day, tpl.hora_inicio, tzinfo=zone)
        end_bound = datetime.datetime.combine(target_day, tpl.hora_fin, tzinfo=zone)
        step = datetime.timedelta(minutes=tpl.duracion_slot_minutos)
        while cursor + step <= end_bound:
            candidates.append((cursor, cursor + step))
            cursor += step

    preferred_dt = datetime.datetime.combine(target_day, preferred_time, tzinfo=zone)
    candidates.sort(key=lambda pair: (pair[0] < preferred_dt, pair[0]))
    return candidates


async def seed_calendar_demo(
    session: AsyncSession,
    base_date: datetime.date | None = None,
    timezone_str: str = DEFAULT_CLINIC_TIMEZONE,
) -> dict[str, int]:
    """Idempotently add a moderate set of synthetic appointments across weekdays of the current month."""
    zone = ZoneInfo(timezone_str)
    ref_date = base_date or datetime.datetime.now(zone).date()

    users_stmt = select(Usuario).where(
        Usuario.email.in_([*DEMO_DENTIST_EMAILS, *DEMO_PATIENT_EMAILS])
    )
    users_by_email = {u.email: u for u in (await session.scalars(users_stmt)).all()}

    for email in (*DEMO_DENTIST_EMAILS, *DEMO_PATIENT_EMAILS):
        if email not in users_by_email:
            raise RuntimeError(
                f"Falta el usuario base '{email}'. Ejecutá primero `python -m scripts.seed`."
            )

    sofia = users_by_email[DEMO_DENTIST_EMAILS[0]]
    lucas = users_by_email[DEMO_DENTIST_EMAILS[1]]
    carlos = users_by_email[DEMO_PATIENT_EMAILS[0]]
    lucia = users_by_email[DEMO_PATIENT_EMAILS[1]]

    if sofia.rol != RolUsuario.ODONTOLOGO or lucas.rol != RolUsuario.ODONTOLOGO:
        raise RuntimeError("Los usuarios de odontología base no tienen el rol esperado.")

    tpl_stmt = select(PlantillaDisponibilidad).where(
        PlantillaDisponibilidad.odontologo_id.in_([sofia.id, lucas.id])
    )
    all_templates = list((await session.scalars(tpl_stmt)).all())
    templates_by_dentist: dict[int, list[PlantillaDisponibilidad]] = {
        sofia.id: [t for t in all_templates if t.odontologo_id == sofia.id],
        lucas.id: [t for t in all_templates if t.odontologo_id == lucas.id],
    }
    if not templates_by_dentist[sofia.id] or not templates_by_dentist[lucas.id]:
        raise RuntimeError(
            "Faltan plantillas de disponibilidad base. Ejecutá primero `python -m scripts.seed`."
        )

    days = _select_month_weekdays(ref_date, count=4)
    if not days:
        return {"creados": 0, "omitidos": 0}

    # 7 synthetic appointments across 4 weekdays (1-2 per day, never flooding the calendar)
    plan = [
        (days[0], datetime.time(10, 0), sofia, carlos, EstadoTurno.CONFIRMADO, "Control periodontal"),
        (days[0], datetime.time(15, 0), lucas, lucia, EstadoTurno.SOLICITADO, "Evaluación ortodoncia"),
        (days[min(1, len(days) - 1)], datetime.time(11, 0), sofia, lucia, EstadoTurno.CONFIRMADO, "Limpieza preventiva"),
        (days[min(1, len(days) - 1)], datetime.time(14, 30), sofia, carlos, EstadoTurno.SOLICITADO, "Consulta estética"),
        (days[min(2, len(days) - 1)], datetime.time(9, 30), lucas, carlos, EstadoTurno.CONFIRMADO, "Control de placa"),
        (days[min(2, len(days) - 1)], datetime.time(16, 0), lucas, lucia, EstadoTurno.CONFIRMADO, "Radiografía de control"),
        (days[min(3, len(days) - 1)], datetime.time(16, 30), sofia, lucia, EstadoTurno.CONFIRMADO, "Control post-tratamiento"),
    ]
    demo_motivos = {item[5] for item in plan}

    month_start = datetime.datetime(ref_date.year, ref_date.month, 1, 0, 0, tzinfo=zone)
    next_month = (
        datetime.datetime(ref_date.year + 1, 1, 1, 0, 0, tzinfo=zone)
        if ref_date.month == 12
        else datetime.datetime(ref_date.year, ref_date.month + 1, 1, 0, 0, tzinfo=zone)
    )
    existing_stmt = select(Turno).where(
        Turno.odontologo_id.in_([sofia.id, lucas.id]),
        Turno.inicio >= month_start,
        Turno.inicio < next_month,
    )
    existing_turnos = list((await session.scalars(existing_stmt)).all())

    active_intervals: dict[int, list[tuple[datetime.datetime, datetime.datetime]]] = {
        sofia.id: [],
        lucas.id: [],
    }
    existing_demo_keys: set[tuple[int, str]] = set()
    for t in existing_turnos:
        if EstadoTurno(t.estado) in (EstadoTurno.CANCELADO, EstadoTurno.ANULADO):
            continue
        active_intervals[t.odontologo_id].append(
            (_normalize_dt(t.inicio, zone), _normalize_dt(t.fin, zone))
        )
        if t.motivo in demo_motivos:
            existing_demo_keys.add((t.odontologo_id, t.motivo))

    creados = 0
    omitidos = 0
    for target_day, preferred_t, dentist, patient, estado, motivo in plan:
        if (dentist.id, motivo) in existing_demo_keys:
            omitidos += 1
            continue

        chosen: tuple[datetime.datetime, datetime.datetime] | None = None
        for cand_start, cand_end in _iter_day_slots(
            templates_by_dentist[dentist.id],
            target_day,
            preferred_t,
            zone,
        ):
            overlaps = any(
                cand_start < ex_end and cand_end > ex_start
                for ex_start, ex_end in active_intervals[dentist.id]
            )
            if not overlaps:
                chosen = (cand_start, cand_end)
                break

        if chosen is None:
            omitidos += 1
            continue

        nuevo_turno = Turno(
            paciente_id=patient.id,
            odontologo_id=dentist.id,
            inicio=chosen[0],
            fin=chosen[1],
            motivo=motivo,
            estado=estado,
            origen=OrigenTurno.ONLINE,
        )
        session.add(nuevo_turno)
        active_intervals[dentist.id].append(chosen)
        existing_demo_keys.add((dentist.id, motivo))
        creados += 1

    await session.commit()
    return {"creados": creados, "omitidos": omitidos}
