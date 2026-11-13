from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import init_engine, init_session_factory
from app.infrastructure.security import LoginRateLimiter


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
    app.state.settings = app_settings
    app.state.login_rate_limiter = LoginRateLimiter()

    from app.api.health import router as health_router
    from app.api.auth import router as auth_router
    from app.api.plantillas import router as plantillas_router
    from app.api.disponibilidad import router as disponibilidad_router
    from app.api.turnos import router as turnos_router
    from app.api.mis_turnos import router as mis_turnos_router
    from app.api.agenda import router as agenda_router
    from app.api.odontologos import router as odontologos_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(plantillas_router)
    app.include_router(disponibilidad_router)
    app.include_router(turnos_router)
    app.include_router(mis_turnos_router)
    app.include_router(agenda_router)
    app.include_router(odontologos_router)

    return app


# Module-level app instance created for ASGI servers (e.g. uvicorn app.main:app)
try:
    app = create_app()
except Exception:
    # Allows importing app.main in environments where .env is not yet configured
    pass
