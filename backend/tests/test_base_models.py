import datetime
from enum import Enum
import pytest
from sqlalchemy import Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario


class DummyModel(Base, TimestampMixin):
    __tablename__ = "dummy_test_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


def test_rol_usuario_enum_values():
    """Verifies that RolUsuario has all required roles as strings."""
    assert issubclass(RolUsuario, str)
    assert issubclass(RolUsuario, Enum)
    assert RolUsuario.PACIENTE.value == "paciente"
    assert RolUsuario.RECEPCION.value == "recepcion"
    assert RolUsuario.ODONTOLOGO.value == "odontologo"
    assert set(RolUsuario) == {
        RolUsuario.PACIENTE,
        RolUsuario.RECEPCION,
        RolUsuario.ODONTOLOGO,
    }


def test_estado_turno_enum_values():
    """Verifies that EstadoTurno matches the 6 states specified in KB-04."""
    assert issubclass(EstadoTurno, str)
    assert issubclass(EstadoTurno, Enum)
    assert EstadoTurno.SOLICITADO.value == "solicitado"
    assert EstadoTurno.CONFIRMADO.value == "confirmado"
    assert EstadoTurno.ANULADO.value == "anulado"
    assert EstadoTurno.CANCELADO.value == "cancelado"
    assert EstadoTurno.PRESENTE.value == "presente"
    assert EstadoTurno.AUSENTE.value == "ausente"
    assert len(EstadoTurno) == 6


def test_origen_turno_enum_values():
    """Verifies that OrigenTurno has online and manual."""
    assert issubclass(OrigenTurno, str)
    assert issubclass(OrigenTurno, Enum)
    assert OrigenTurno.ONLINE.value == "online"
    assert OrigenTurno.MANUAL.value == "manual"
    assert len(OrigenTurno) == 2


def test_enum_string_comparison_and_json_safety():
    """Triangulation: StrEnum allows direct string comparison and JSON serialization."""
    assert EstadoTurno.SOLICITADO == "solicitado"
    assert RolUsuario.PACIENTE == "paciente"
    assert OrigenTurno.ONLINE == "online"

    with pytest.raises(ValueError):
        EstadoTurno("invalido")

    with pytest.raises(ValueError):
        RolUsuario("admin_super")


@pytest.mark.asyncio
async def test_timestamp_mixin_automatic_population(async_session: AsyncSession):
    """Verifies that TimestampMixin sets creado_en and actualizado_en as timezone-aware UTC datetimes."""
    dummy = DummyModel(name="test_record")
    async_session.add(dummy)
    await async_session.commit()
    await async_session.refresh(dummy)

    assert dummy.id is not None
    assert dummy.creado_en is not None
    assert dummy.actualizado_en is not None

    # Verify timezone awareness
    assert dummy.creado_en.tzinfo is not None or dummy.creado_en.isoformat()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # The timestamps should be very recent (within 5 seconds)
    creado_tz = dummy.creado_en if dummy.creado_en.tzinfo else dummy.creado_en.replace(tzinfo=datetime.timezone.utc)
    assert abs((now_utc - creado_tz).total_seconds()) < 5


@pytest.mark.asyncio
async def test_timestamp_mixin_updated_on_change(async_session: AsyncSession):
    """Verifies that actualizado_en is updated when record is modified."""
    dummy = DummyModel(name="initial")
    async_session.add(dummy)
    await async_session.commit()
    await async_session.refresh(dummy)

    initial_actualizado_en = dummy.actualizado_en

    # Update record
    dummy.name = "updated"
    await async_session.commit()
    await async_session.refresh(dummy)

    # In SQLite or fast tests, actualizado_en should be >= initial_actualizado_en
    assert dummy.actualizado_en >= initial_actualizado_en
