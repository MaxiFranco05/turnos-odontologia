import datetime
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def sample_users(async_session: AsyncSession):
    paciente = Usuario(
        nombre="Paciente Prueba",
        email="paciente_prueba@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.PACIENTE,
    )
    odontologo = Usuario(
        nombre="Dra. Odontologa Prueba",
        email="odontologa_prueba@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.ODONTOLOGO,
    )
    async_session.add_all([paciente, odontologo])
    await async_session.commit()
    await async_session.refresh(paciente)
    await async_session.refresh(odontologo)
    return paciente, odontologo


@pytest.mark.asyncio
async def test_plantilla_valid_creation(async_session: AsyncSession, sample_users):
    """Scenario: Valid PlantillaDisponibilidad creation."""
    _, odontologo = sample_users

    plantilla = PlantillaDisponibilidad(
        odontologo_id=odontologo.id,
        dia_semana=1,  # Martes
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(13, 0),
        duracion_slot_minutos=30,
        prestacion="Consulta General",
    )
    async_session.add(plantilla)
    await async_session.commit()
    await async_session.refresh(plantilla)

    assert plantilla.id is not None
    assert plantilla.odontologo_id == odontologo.id
    assert plantilla.duracion_slot_minutos == 30
    assert plantilla.odontologo.nombre == "Dra. Odontologa Prueba"


@pytest.mark.asyncio
async def test_plantilla_rejects_inverted_hours(async_session: AsyncSession, sample_users):
    """Scenario: PlantillaDisponibilidad rejects hora_fin <= hora_inicio."""
    _, odontologo = sample_users

    plantilla = PlantillaDisponibilidad(
        odontologo_id=odontologo.id,
        dia_semana=1,
        hora_inicio=datetime.time(14, 0),
        hora_fin=datetime.time(10, 0),  # Inverted!
        duracion_slot_minutos=30,
    )
    async_session.add(plantilla)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_plantilla_rejects_non_positive_duration(async_session: AsyncSession, sample_users):
    """Scenario: PlantillaDisponibilidad rejects duracion_slot_minutos <= 0."""
    _, odontologo = sample_users

    plantilla = PlantillaDisponibilidad(
        odontologo_id=odontologo.id,
        dia_semana=1,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(13, 0),
        duracion_slot_minutos=0,  # Invalid!
    )
    async_session.add(plantilla)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_plantilla_rejects_invalid_day_of_week(async_session: AsyncSession, sample_users):
    """Scenario: PlantillaDisponibilidad rejects dia_semana outside [0, 6]."""
    _, odontologo = sample_users

    plantilla = PlantillaDisponibilidad(
        odontologo_id=odontologo.id,
        dia_semana=7,  # Invalid day!
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(13, 0),
        duracion_slot_minutos=30,
    )
    async_session.add(plantilla)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_turno_valid_creation(async_session: AsyncSession, sample_users):
    """Scenario: Valid Turno creation with defaults and relationships."""
    paciente, odontologo = sample_users
    inicio = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    fin = inicio + datetime.timedelta(minutes=30)

    turno = Turno(
        paciente_id=paciente.id,
        odontologo_id=odontologo.id,
        inicio=inicio,
        fin=fin,
        motivo="Limpieza y control semestral",
    )
    async_session.add(turno)
    await async_session.commit()
    await async_session.refresh(turno)

    assert turno.id is not None
    assert turno.estado == EstadoTurno.SOLICITADO
    assert turno.origen == OrigenTurno.ONLINE
    assert turno.paciente.email == "paciente_prueba@example.com"
    assert turno.odontologo.email == "odontologa_prueba@example.com"
    assert turno.creado_en is not None
    assert turno.actualizado_en is not None


@pytest.mark.asyncio
async def test_turno_rejects_inverted_timestamps(async_session: AsyncSession, sample_users):
    """Scenario: Turno rejects fin < inicio (check constraint)."""
    paciente, odontologo = sample_users
    inicio = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    turno_invertido = Turno(
        paciente_id=paciente.id,
        odontologo_id=odontologo.id,
        inicio=inicio,
        fin=inicio - datetime.timedelta(minutes=30),
        motivo="Consulta Invertida",
    )
    async_session.add(turno_invertido)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_turno_rejects_equal_timestamps(async_session: AsyncSession, sample_users):
    """Scenario: Turno rejects fin == inicio (check constraint)."""
    paciente, odontologo = sample_users
    inicio = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

    turno_igual = Turno(
        paciente_id=paciente.id,
        odontologo_id=odontologo.id,
        inicio=inicio,
        fin=inicio,
        motivo="Consulta Cero Duracion",
    )
    async_session.add(turno_igual)
    with pytest.raises(IntegrityError):
        await async_session.commit()
