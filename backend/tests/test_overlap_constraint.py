import datetime
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, RolUsuario
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
async def test_actors(async_session: AsyncSession):
    paciente = Usuario(
        nombre="Paciente Sintetico",
        email="paciente_overlap@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.PACIENTE,
    )
    paciente2 = Usuario(
        nombre="Paciente Dos",
        email="paciente2_overlap@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.PACIENTE,
    )
    odontologo1 = Usuario(
        nombre="Dr. Odontologo Uno",
        email="odontologo1_overlap@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.ODONTOLOGO,
    )
    odontologo2 = Usuario(
        nombre="Dra. Odontologa Dos",
        email="odontologo2_overlap@example.com",
        password_hash="pw_hash_test",
        rol=RolUsuario.ODONTOLOGO,
    )
    async_session.add_all([paciente, paciente2, odontologo1, odontologo2])
    await async_session.commit()
    await async_session.refresh(paciente)
    await async_session.refresh(paciente2)
    await async_session.refresh(odontologo1)
    await async_session.refresh(odontologo2)
    return {
        "paciente": paciente,
        "paciente2": paciente2,
        "odontologo1": odontologo1,
        "odontologo2": odontologo2,
    }


@pytest.mark.asyncio
async def test_consecutive_non_overlapping_appointments_accepted(async_session: AsyncSession, test_actors):
    """Scenario: Two consecutive appointments for the same dentist are accepted."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]

    base_time = datetime.datetime(2026, 11, 10, 9, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Consulta 1",
    )
    t2 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(minutes=30),
        fin=base_time + datetime.timedelta(minutes=60),
        motivo="Consulta 2",
    )
    async_session.add_all([t1, t2])
    await async_session.commit()

    assert t1.id is not None
    assert t2.id is not None


@pytest.mark.asyncio
async def test_simultaneous_appointments_different_dentists_accepted(async_session: AsyncSession, test_actors):
    """Scenario: Simultaneous appointments for DIFFERENT dentists are accepted."""
    odo1 = test_actors["odontologo1"]
    odo2 = test_actors["odontologo2"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 10, 10, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo1.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Consulta Odo 1",
    )
    t2 = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo2.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Consulta Odo 2",
    )
    async_session.add_all([t1, t2])
    await async_session.commit()

    assert t1.id is not None
    assert t2.id is not None


@pytest.mark.asyncio
async def test_overlapping_appointment_same_dentist_rejected(async_session: AsyncSession, test_actors):
    """Scenario: Overlapping appointment for the SAME dentist is rejected (RN-AG-01)."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 10, 11, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Turno Inicial",
    )
    async_session.add(t1)
    await async_session.commit()

    # Attempt to insert an intersecting appointment: 11:15 - 11:45
    t2_intersect = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(minutes=15),
        fin=base_time + datetime.timedelta(minutes=45),
        motivo="Turno Solapado",
    )
    async_session.add(t2_intersect)
    with pytest.raises((IntegrityError, ValueError)):
        await async_session.commit()


@pytest.mark.asyncio
async def test_contained_overlap_same_dentist_rejected(async_session: AsyncSession, test_actors):
    """Scenario: Contained appointment (inside an existing window) is rejected."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 10, 14, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(hours=1),
        motivo="Turno Largo",
    )
    async_session.add(t1)
    await async_session.commit()

    t2 = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(minutes=10),
        fin=base_time + datetime.timedelta(minutes=40),
        motivo="Turno Interior",
    )
    async_session.add(t2)
    with pytest.raises((IntegrityError, ValueError)):
        await async_session.commit()


@pytest.mark.asyncio
async def test_overlap_allowed_if_previous_cancelled_or_annulled(async_session: AsyncSession, test_actors):
    """Scenario: Overlapping is accepted if earlier appointment was cancelado or anulado."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 10, 16, 0, tzinfo=datetime.timezone.utc)
    t_cancelado = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Turno Cancelado por Paciente",
        estado=EstadoTurno.CANCELADO,
    )
    async_session.add(t_cancelado)
    await async_session.commit()

    # Re-booking the same slot should succeed
    t_nuevo = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Nuevo Turno en Hueco Liberado",
        estado=EstadoTurno.SOLICITADO,
    )
    async_session.add(t_nuevo)
    await async_session.commit()

    assert t_nuevo.id is not None


@pytest.mark.asyncio
async def test_update_appointment_to_overlap_rejected(async_session: AsyncSession, test_actors):
    """Triangulation: Updating an existing appointment to an overlapping time is rejected."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 10, 18, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Turno Tarde 1",
    )
    t2 = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(hours=2),
        fin=base_time + datetime.timedelta(hours=2, minutes=30),
        motivo="Turno Tarde 2",
    )
    async_session.add_all([t1, t2])
    await async_session.commit()

    # Move t2 into t1's interval
    t2.inicio = base_time + datetime.timedelta(minutes=15)
    t2.fin = base_time + datetime.timedelta(minutes=45)
    with pytest.raises((IntegrityError, ValueError)):
        await async_session.commit()


@pytest.mark.asyncio
async def test_update_appointment_non_time_field_allowed(async_session: AsyncSession, test_actors):
    """Triangulation: Updating non-time fields of an existing appointment succeeds (no self-collision)."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]

    base_time = datetime.datetime(2026, 11, 10, 20, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Motivo Original",
    )
    async_session.add(t1)
    await async_session.commit()

    t1.motivo = "Motivo Modificado"
    await async_session.commit()
    await async_session.refresh(t1)

    assert t1.motivo == "Motivo Modificado"


@pytest.mark.asyncio
async def test_overlap_allowed_if_previous_annulled(async_session: AsyncSession, test_actors):
    """Triangulation: Overlap allowed if conflicting appointment was anulado by recepcion."""
    odo = test_actors["odontologo1"]
    pac = test_actors["paciente"]
    pac2 = test_actors["paciente2"]

    base_time = datetime.datetime(2026, 11, 11, 10, 0, tzinfo=datetime.timezone.utc)
    t_anulado = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Turno Anulado por Recepcion",
        estado=EstadoTurno.ANULADO,
    )
    async_session.add(t_anulado)
    await async_session.commit()

    t_nuevo = Turno(
        paciente_id=pac2.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Nuevo Turno Paciente 2",
        estado=EstadoTurno.SOLICITADO,
    )
    async_session.add(t_nuevo)
    await async_session.commit()

    assert t_nuevo.id is not None

