import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.seed import seed_data
from app.infrastructure.seed_calendar_demo import seed_calendar_demo

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


@pytest.fixture
async def db_session():
    """Real SQLite in-memory DB session without mocks (Hard Rule #7)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_calendar_demo_requires_base_seed(db_session: AsyncSession):
    """C-22 Task 2.1: Fails clearly if base users/templates from scripts.seed are missing."""
    with pytest.raises(RuntimeError, match="scripts.seed"):
        await seed_calendar_demo(session=db_session, base_date=datetime.date(2026, 11, 13))


@pytest.mark.asyncio
async def test_seed_calendar_demo_creates_moderate_non_overlapping_appointments_and_is_idempotent(
    db_session: AsyncSession,
):
    """C-22 Task 2.1 (RN-AG-01, RN-AG-02, CB-02, CB-04): Adds 6-8 valid demo appointments and is idempotent."""
    fixed_date = datetime.date(2026, 11, 13)  # Friday mid-month
    await seed_data(session=db_session, reset=False, base_date=fixed_date)

    first_run = await seed_calendar_demo(session=db_session, base_date=fixed_date)
    assert 6 <= first_run["creados"] <= 8
    assert first_run["omitidos"] == 0

    turnos = list(
        (await db_session.scalars(select(Turno).order_by(Turno.odontologo_id, Turno.inicio))).all()
    )
    # 4 canonical from seed.py + 6..8 from seed_calendar_demo
    assert len(turnos) == 4 + first_run["creados"]

    dentists = list(
        (await db_session.scalars(select(Usuario).where(Usuario.rol == RolUsuario.ODONTOLOGO))).all()
    )
    patients = list(
        (await db_session.scalars(select(Usuario).where(Usuario.rol == RolUsuario.PACIENTE))).all()
    )
    dentist_ids = {d.id for d in dentists}
    patient_ids = {p.id for p in patients}

    # Verify both dentists and both patients received appointments, and mixed states exist
    assert {t.odontologo_id for t in turnos} == dentist_ids
    assert {t.paciente_id for t in turnos} == patient_ids
    estados = {t.estado for t in turnos}
    assert EstadoTurno.CONFIRMADO in estados
    assert EstadoTurno.SOLICITADO in estados

    # Verify spread across at least 3 distinct weekdays in the target month
    distinct_dates = {t.inicio.astimezone(AR_TZ).date() for t in turnos}
    assert len(distinct_dates) >= 3
    for d in distinct_dates:
        assert d.year == fixed_date.year
        assert d.month == fixed_date.month
        assert d.weekday() < 5

    # Verify alignment to PlantillaDisponibilidad (30 min slots) and zero overlap per dentist
    plantillas = list((await db_session.scalars(select(PlantillaDisponibilidad))).all())
    for dentist in dentists:
        dentist_turnos = [t for t in turnos if t.odontologo_id == dentist.id]
        dentist_templates = [p for p in plantillas if p.odontologo_id == dentist.id]
        for idx, t in enumerate(dentist_turnos):
            start_local = t.inicio.astimezone(AR_TZ)
            end_local = t.fin.astimezone(AR_TZ)
            assert (end_local - start_local) == datetime.timedelta(minutes=30)
            matching_tpl = [
                p
                for p in dentist_templates
                if p.dia_semana == start_local.weekday()
                and p.hora_inicio <= start_local.time()
                and end_local.time() <= p.hora_fin
            ]
            assert matching_tpl, f"Turno {t.id} fuera de plantilla: {start_local}..{end_local}"
            if idx > 0:
                prev = dentist_turnos[idx - 1]
                assert prev.fin <= t.inicio, "Solapamiento detectado entre turnos"

    # Second execution must be 100% idempotent
    second_run = await seed_calendar_demo(session=db_session, base_date=fixed_date)
    assert second_run["creados"] == 0
    assert second_run["omitidos"] == first_run["creados"]

    turnos_after = list((await db_session.scalars(select(Turno))).all())
    assert len(turnos_after) == len(turnos)


@pytest.mark.asyncio
async def test_seed_calendar_demo_handles_month_end_gracefully(db_session: AsyncSession):
    """C-22 Task 2.1 (Triangulate month-end): Stays within target month even on last weekday of month."""
    month_end_date = datetime.date(2026, 11, 30)  # Last day of Nov 2026 (Monday)
    await seed_data(session=db_session, reset=False, base_date=month_end_date)

    res = await seed_calendar_demo(session=db_session, base_date=month_end_date)
    assert 6 <= res["creados"] <= 8

    turnos = list((await db_session.scalars(select(Turno))).all())
    nov_dates = {
        t.inicio.astimezone(AR_TZ).date()
        for t in turnos
        if t.inicio.astimezone(AR_TZ).month == 11
    }
    assert len(nov_dates) >= 3
