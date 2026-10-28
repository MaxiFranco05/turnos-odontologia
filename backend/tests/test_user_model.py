import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import RolUsuario
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


@pytest.mark.asyncio
async def test_usuario_creation_with_email(async_session: AsyncSession):
    """Scenario: User creation with email identifier."""
    user = Usuario(
        nombre="Paciente Sintetico Uno",
        email="paciente1@example.com",
        password_hash="hashed_pw_dummy",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    assert user.id is not None
    assert user.email == "paciente1@example.com"
    assert user.nro_socio is None
    assert user.debe_cambiar_password is True
    assert user.perfil_completo is False
    assert user.rol == RolUsuario.PACIENTE
    assert user.creado_en is not None
    assert user.actualizado_en is not None


@pytest.mark.asyncio
async def test_usuario_creation_with_nro_socio(async_session: AsyncSession):
    """Scenario: User creation with nro_socio identifier."""
    user = Usuario(
        nombre="Paciente Socio Dos",
        nro_socio="SOC-12345",
        password_hash="hashed_pw_dummy",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    assert user.id is not None
    assert user.nro_socio == "SOC-12345"
    assert user.email is None


@pytest.mark.asyncio
async def test_usuario_creation_with_both_identifiers(async_session: AsyncSession):
    """Scenario: User creation with both email and nro_socio."""
    user = Usuario(
        nombre="Odontologo Sintetico",
        email="odontologo@example.com",
        nro_socio="ODO-999",
        password_hash="hashed_pw_dummy",
        rol=RolUsuario.ODONTOLOGO,
        debe_cambiar_password=False,
        perfil_completo=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    assert user.email == "odontologo@example.com"
    assert user.nro_socio == "ODO-999"
    assert user.debe_cambiar_password is False
    assert user.perfil_completo is True


@pytest.mark.asyncio
async def test_usuario_creation_fails_without_identifier(async_session: AsyncSession):
    """Scenario: User creation without email and without nro_socio fails constraint."""
    user = Usuario(
        nombre="Sin Identificador",
        email=None,
        nro_socio=None,
        password_hash="hashed_pw_dummy",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(user)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_usuario_unique_email_constraint(async_session: AsyncSession):
    """Scenario: Duplicate email is rejected."""
    user1 = Usuario(
        nombre="User A",
        email="duplicado@example.com",
        password_hash="hash_a",
        rol=RolUsuario.PACIENTE,
    )
    user2 = Usuario(
        nombre="User B",
        email="duplicado@example.com",
        password_hash="hash_b",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(user1)
    await async_session.commit()

    async_session.add(user2)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_usuario_unique_nro_socio_constraint(async_session: AsyncSession):
    """Scenario: Duplicate nro_socio is rejected."""
    user1 = Usuario(
        nombre="User A",
        nro_socio="SOC-DUP-1",
        password_hash="hash_a",
        rol=RolUsuario.PACIENTE,
    )
    user2 = Usuario(
        nombre="User B",
        nro_socio="SOC-DUP-1",
        password_hash="hash_b",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(user1)
    await async_session.commit()

    async_session.add(user2)
    with pytest.raises(IntegrityError):
        await async_session.commit()
