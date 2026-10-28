from collections.abc import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def init_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Initializes and returns an asynchronous SQLAlchemy 2.0 engine.
    
    Uses pool_pre_ping=True to guard against stale connections and reconnect automatically.
    """
    return create_async_engine(
        database_url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
    )


def init_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates a thread-safe asynchronous session factory."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Yields an AsyncSession and ensures proper commit/rollback and cleanup."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI request dependency that resolves the session factory from app.state."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async for session in get_db_session(session_factory):
        yield session
