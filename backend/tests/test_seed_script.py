import datetime
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.security import verify_password
from app.infrastructure.seed import seed_data

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


@pytest.fixture
async def db_session():
    """Provides a fresh real SQLite in-memory database session without mocks (Hard Rule #7)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_data_creates_all_entities_and_verifies_credentials(db_session: AsyncSession):
    """Task 1.1 / Req 1 & 2: Initial seeding creates reception, dentists, patients, templates, and appointments."""
    fixed_date = datetime.date(2027, 3, 1)  # A Monday

    counts = await seed_data(session=db_session, reset=False, base_date=fixed_date)

    # 1. Verify counts returned
    assert counts["usuarios"] == 5
    assert counts["plantillas"] == 20  # 2 dentists * 5 weekdays * 2 shifts (morning & afternoon)
    assert counts["turnos"] == 4

    # 2. Verify reception user and security flags (RN-AU-01 & US-001)
    reception_stmt = select(Usuario).where(Usuario.rol == RolUsuario.RECEPCION)
    reception = await db_session.scalar(reception_stmt)
    assert reception is not None
    assert reception.email == "recepcion@turnosodontologia.com"
    assert reception.debe_cambiar_password is True
    assert reception.perfil_completo is True
    assert verify_password("Admin1234!", reception.password_hash) is True

    # 3. Verify dentists and passwords
    dentists_stmt = select(Usuario).where(Usuario.rol == RolUsuario.ODONTOLOGO).order_by(Usuario.id)
    dentists = list((await db_session.scalars(dentists_stmt)).all())
    assert len(dentists) == 2
    for dentist in dentists:
        assert dentist.debe_cambiar_password is False
        assert dentist.perfil_completo is True
        assert verify_password("Dentist1234!", dentist.password_hash) is True
        assert dentist.nro_socio in ("ODO-001", "ODO-002")

    # 4. Verify patients
    patients_stmt = select(Usuario).where(Usuario.rol == RolUsuario.PACIENTE).order_by(Usuario.id)
    patients = list((await db_session.scalars(patients_stmt)).all())
    assert len(patients) == 2
    for patient in patients:
        assert verify_password("Patient1234!", patient.password_hash) is True
        assert patient.nro_socio in ("SOC-101", "SOC-102")

    # 5. Verify availability templates (RN-AG-01: no overlapping slots)
    for dentist in dentists:
        templates_stmt = (
            select(PlantillaDisponibilidad)
            .where(PlantillaDisponibilidad.odontologo_id == dentist.id)
            .order_by(PlantillaDisponibilidad.dia_semana, PlantillaDisponibilidad.hora_inicio)
        )
        templates = list((await db_session.scalars(templates_stmt)).all())
        assert len(templates) == 10  # 5 days * 2 shifts
        for t in templates:
            assert t.duracion_slot_minutos == 30
            assert t.hora_fin > t.hora_inicio
            assert t.dia_semana in range(0, 5)

    # 6. Verify demonstration appointments and states (Hard Rule #13)
    turnos_stmt = select(Turno).order_by(Turno.inicio)
    turnos = list((await db_session.scalars(turnos_stmt)).all())
    assert len(turnos) == 4
    estados = {t.estado for t in turnos}
    assert EstadoTurno.CONFIRMADO in estados
    assert EstadoTurno.SOLICITADO in estados
    assert EstadoTurno.CANCELADO in estados


@pytest.mark.asyncio
async def test_seed_data_is_strictly_idempotent(db_session: AsyncSession):
    """Task 1.1 / Req 4: Running seed_data repeatedly produces identical state without duplicates or errors."""
    fixed_date = datetime.date(2027, 3, 1)

    # First run
    counts1 = await seed_data(session=db_session, reset=False, base_date=fixed_date)
    assert counts1["usuarios"] == 5
    assert counts1["plantillas"] == 20
    assert counts1["turnos"] == 4

    # Second run immediately following the first
    counts2 = await seed_data(session=db_session, reset=False, base_date=fixed_date)
    assert counts2["usuarios"] == 5
    assert counts2["plantillas"] == 20
    assert counts2["turnos"] == 4

    # Total database rows remain unchanged
    all_users = list((await db_session.scalars(select(Usuario))).all())
    all_templates = list((await db_session.scalars(select(PlantillaDisponibilidad))).all())
    all_turnos = list((await db_session.scalars(select(Turno))).all())

    assert len(all_users) == 5
    assert len(all_templates) == 20
    assert len(all_turnos) == 4


@pytest.mark.asyncio
async def test_seed_data_reset_clears_and_recreates_cleanly(db_session: AsyncSession):
    """Task 1.1 / Req 4: reset=True purges entities in reverse FK order and recreates baseline demo data."""
    fixed_date = datetime.date(2027, 3, 1)

    # First run
    await seed_data(session=db_session, reset=False, base_date=fixed_date)

    # Run with reset=True
    counts_reset = await seed_data(session=db_session, reset=True, base_date=fixed_date)
    assert counts_reset["usuarios"] == 5
    assert counts_reset["plantillas"] == 20
    assert counts_reset["turnos"] == 4

    all_users = list((await db_session.scalars(select(Usuario))).all())
    assert len(all_users) == 5


@pytest.mark.asyncio
async def test_seed_data_default_date_and_partial_presence(db_session: AsyncSession):
    """Triangulation: seed_data computes next Monday by default and handles pre-existing accounts gracefully."""
    # Pre-seed one patient manually
    existing_patient = Usuario(
        nombre="Carlos Benítez (Ficticio)",
        email="carlos.benitez@example.com",
        nro_socio="SOC-101",
        password_hash="any_hash",
        rol=RolUsuario.PACIENTE,
        debe_cambiar_password=False,
        perfil_completo=True,
    )
    db_session.add(existing_patient)
    await db_session.commit()

    # Run seed_data without base_date (uses next Monday calculation)
    counts = await seed_data(session=db_session, reset=False, base_date=None)
    assert counts["usuarios"] == 5
    assert counts["plantillas"] == 20
    assert counts["turnos"] == 4

    # Verify seeded appointments land on Monday (weekday() == 0)
    turnos = list((await db_session.scalars(select(Turno))).all())
    for t in turnos:
        assert t.inicio.weekday() == 0


def test_cli_parse_args():
    """Task 2.1: CLI argument parser correctly interprets --reset and --date."""
    from scripts.seed import parse_args

    args_default = parse_args([])
    assert args_default.reset is False
    assert args_default.date is None

    args_custom = parse_args(["--reset", "--date", "2027-05-10"])
    assert args_custom.reset is True
    assert args_custom.date == "2027-05-10"

