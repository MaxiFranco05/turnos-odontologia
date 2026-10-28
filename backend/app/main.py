from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import init_engine, init_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI application factory.
    
    Accepts custom or test settings; falls back to cached get_settings().
    """
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Manages application startup and graceful shutdown."""
        engine = init_engine(app_settings.async_database_url, echo=app_settings.DEBUG)
        session_factory = init_session_factory(engine)

        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.settings = app_settings

        yield

        # Graceful shutdown: release all connection pool resources
        await engine.dispose()

    app = FastAPI(
        title=app_settings.APP_NAME,
        debug=app_settings.DEBUG,
        lifespan=lifespan,
    )

    from app.api.health import router as health_router
    app.include_router(health_router)

    return app


# Module-level app instance created for ASGI servers (e.g. uvicorn app.main:app)
try:
    app = create_app()
except Exception:
    # Allows importing app.main in environments where .env is not yet configured
    app = None  # type: ignore[assignment]
