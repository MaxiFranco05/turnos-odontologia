import datetime
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.plantilla import SqlAlchemyPlantillaRepository
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository


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
async def seeded_data(async_session: AsyncSession):
    paciente = Usuario(
        nombre="Paciente Repo",
        email="paciente_repo@example.com",
        nro_socio="SOC-REPO-1",
        password_hash="pw_hash",
        rol=RolUsuario.PACIENTE,
    )
    odontologo = Usuario(
        nombre="Dr. Odontologo Repo",
        email="odontologo_repo@example.com",
        nro_socio="ODO-REPO-1",
        password_hash="pw_hash",
        rol=RolUsuario.ODONTOLOGO,
    )
    recepcionista = Usuario(
        nombre="Recepcion Repo",
        email="recepcion_repo@example.com",
        password_hash="pw_hash",
        rol=RolUsuario.RECEPCION,
    )
    async_session.add_all([paciente, odontologo, recepcionista])
    await async_session.commit()
    await async_session.refresh(paciente)
    await async_session.refresh(odontologo)
    await async_session.refresh(recepcionista)
    return {
        "paciente": paciente,
        "odontologo": odontologo,
        "recepcion": recepcionista,
    }


@pytest.mark.asyncio
async def test_usuario_repository_find_methods(async_session: AsyncSession, seeded_data):
    """Verifies lookup by id, email, nro_socio, and generic identifier."""
    repo = SqlAlchemyUsuarioRepository(async_session)
    pac = seeded_data["paciente"]

    # By ID
    found = await repo.get_by_id(pac.id)
    assert found is not None
    assert found.nombre == "Paciente Repo"

    # By Email
    found_email = await repo.get_by_email("paciente_repo@example.com")
    assert found_email is not None
    assert found_email.id == pac.id

    # By Nro Socio
    found_socio = await repo.get_by_nro_socio("SOC-REPO-1")
    assert found_socio is not None
    assert found_socio.id == pac.id

    # By generic identifier (can be email or nro_socio)
    via_email = await repo.get_by_identifier("paciente_repo@example.com")
    assert via_email is not None
    assert via_email.id == pac.id

    via_socio = await repo.get_by_identifier("SOC-REPO-1")
    assert via_socio is not None
    assert via_socio.id == pac.id

    # Unknown
    assert await repo.get_by_identifier("inexistente") is None


@pytest.mark.asyncio
async def test_usuario_repository_list_by_rol(async_session: AsyncSession, seeded_data):
    """Verifies listing users filtered by role."""
    repo = SqlAlchemyUsuarioRepository(async_session)

    pacientes = await repo.list_by_rol(RolUsuario.PACIENTE)
    assert len(pacientes) == 1
    assert pacientes[0].nombre == "Paciente Repo"

    odontologos = await repo.list_by_rol(RolUsuario.ODONTOLOGO)
    assert len(odontologos) == 1
    assert odontologos[0].nombre == "Dr. Odontologo Repo"


@pytest.mark.asyncio
async def test_turno_repository_range_and_overlap(async_session: AsyncSession, seeded_data):
    """Verifies TurnoRepository query methods for range lookup and overlap detection."""
    repo = SqlAlchemyTurnoRepository(async_session)
    pac = seeded_data["paciente"]
    odo = seeded_data["odontologo"]

    base_time = datetime.datetime(2026, 11, 15, 10, 0, tzinfo=datetime.timezone.utc)
    t1 = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time,
        fin=base_time + datetime.timedelta(minutes=30),
        motivo="Consulta Periodica",
        estado=EstadoTurno.CONFIRMADO,
    )
    t_cancelado = Turno(
        paciente_id=pac.id,
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(hours=2),
        fin=base_time + datetime.timedelta(hours=2, minutes=30),
        motivo="Consulta Cancelada",
        estado=EstadoTurno.CANCELADO,
    )
    await repo.add(t1)
    await repo.add(t_cancelado)
    await async_session.commit()

    # Find by dentist range
    turnos_odo = await repo.find_by_dentist_range(
        odontologo_id=odo.id,
        start=base_time - datetime.timedelta(hours=1),
        end=base_time + datetime.timedelta(hours=5),
    )
    assert len(turnos_odo) == 2

    # Find by patient range
    turnos_pac = await repo.find_by_patient_range(
        paciente_id=pac.id,
        start=base_time - datetime.timedelta(hours=1),
        end=base_time + datetime.timedelta(hours=5),
    )
    assert len(turnos_pac) == 2

    # Check overlap with t1
    has_ov = await repo.has_overlap(
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(minutes=10),
        fin=base_time + datetime.timedelta(minutes=40),
    )
    assert has_ov is True

    # Check overlap excluding t1
    has_ov_excluded = await repo.has_overlap(
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(minutes=10),
        fin=base_time + datetime.timedelta(minutes=40),
        exclude_turno_id=t1.id,
    )
    assert has_ov_excluded is False

    # Check overlap with t_cancelado (should NOT report overlap because cancelled)
    has_ov_cancelled = await repo.has_overlap(
        odontologo_id=odo.id,
        inicio=base_time + datetime.timedelta(hours=2),
        fin=base_time + datetime.timedelta(hours=2, minutes=30),
    )
    assert has_ov_cancelled is False


@pytest.mark.asyncio
async def test_plantilla_repository_methods(async_session: AsyncSession, seeded_data):
    """Verifies PlantillaRepository querying templates by dentist and day of week."""
    repo = SqlAlchemyPlantillaRepository(async_session)
    odo = seeded_data["odontologo"]

    p_lunes = PlantillaDisponibilidad(
        odontologo_id=odo.id,
        dia_semana=0,  # Lunes
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(13, 0),
        duracion_slot_minutos=30,
        prestacion="General",
    )
    p_miercoles = PlantillaDisponibilidad(
        odontologo_id=odo.id,
        dia_semana=2,  # Miercoles
        hora_inicio=datetime.time(14, 0),
        hora_fin=datetime.time(18, 0),
        duracion_slot_minutos=30,
        prestacion="Ortodoncia",
    )
    await repo.add(p_lunes)
    await repo.add(p_miercoles)
    await async_session.commit()

    templates = await repo.find_by_dentist(odo.id)
    assert len(templates) == 2

    lunes_templates = await repo.find_by_dentist_and_day(odo.id, dia_semana=0)
    assert len(lunes_templates) == 1
    assert lunes_templates[0].prestacion == "General"

    martes_templates = await repo.find_by_dentist_and_day(odo.id, dia_semana=1)
    assert len(martes_templates) == 0


@pytest.mark.asyncio
async def test_base_repository_crud_lifecycle(async_session: AsyncSession, seeded_data):
    """Triangulation: Verifies BaseRepository add, list_all, and delete operations."""
    repo = SqlAlchemyUsuarioRepository(async_session)

    new_user = Usuario(
        nombre="Usuario Temporal",
        email="temporal@example.com",
        password_hash="temp_hash",
        rol=RolUsuario.PACIENTE,
    )
    added = await repo.add(new_user)
    assert added.id is not None

    all_users = await repo.list_all()
    # 3 from seeded_data + 1 new
    assert len(all_users) >= 4

    await repo.delete(added)
    assert await repo.get_by_id(added.id) is None

