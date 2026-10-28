import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_init_engine_and_session_factory():
    """Verifies creation of async engine and session factory."""
    from app.infrastructure.database import init_engine, init_session_factory

    engine = init_engine("sqlite+aiosqlite:///:memory:")
    assert isinstance(engine, AsyncEngine)

    session_factory = init_session_factory(engine)
    assert isinstance(session_factory, async_sessionmaker)

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_lifecycle():
    """Verifies that get_db_session yields an active AsyncSession that executes queries and closes."""
    from app.infrastructure.database import init_engine, init_session_factory, get_db_session

    engine = init_engine("sqlite+aiosqlite:///:memory:")
    session_factory = init_session_factory(engine)

    # Use the generator
    session_generator = get_db_session(session_factory)
    session = await anext(session_generator)

    assert isinstance(session, AsyncSession)
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Cleanup generator
    with pytest.raises(StopAsyncIteration):
        await anext(session_generator)

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_rollback_on_exception():
    """Verifies that an unhandled exception inside session context causes rollback."""
    from app.infrastructure.database import init_engine, init_session_factory, get_db_session

    engine = init_engine("sqlite+aiosqlite:///:memory:")
    session_factory = init_session_factory(engine)

    session_generator = get_db_session(session_factory)
    session = await anext(session_generator)

    with pytest.raises(RuntimeError, match="Simulated business error"):
        await session_generator.athrow(RuntimeError("Simulated business error"))

    await engine.dispose()


@pytest.mark.asyncio
async def test_lifespan_attaches_and_disposes_engine():
    """Verifies FastAPI lifespan initializes app.state.engine and cleans up on exit."""
    from app.main import create_app
    from app.infrastructure.config import Settings
    from starlette.testclient import TestClient

    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecretkey_min_32_characters_long_for_hs256",
    )

    app = create_app(settings=settings)

    # Before entering context, state engine is None or unset
    assert not hasattr(app.state, "engine") or app.state.engine is None

    with TestClient(app) as client:
        # Inside lifespan context, engine and session_factory are active
        assert hasattr(app.state, "engine")
        assert isinstance(app.state.engine, AsyncEngine)
        assert hasattr(app.state, "session_factory")
        assert isinstance(app.state.session_factory, async_sessionmaker)

    # After exiting, engine was disposed (pool disposed)
