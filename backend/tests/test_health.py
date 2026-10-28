import pytest
from starlette.testclient import TestClient
from app.infrastructure.config import Settings
from app.main import create_app


def test_health_live_endpoint():
    """Liveness probe returns HTTP 200 and alive payload."""
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecretkey_min_32_characters_long_for_hs256",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


def test_health_ready_endpoint_healthy_db():
    """Readiness probe returns HTTP 200 when database executes ping successfully."""
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecretkey_min_32_characters_long_for_hs256",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "database": "connected"}


def test_health_ready_endpoint_database_failure(monkeypatch):
    """Readiness probe returns HTTP 503 when database connection fails or is unreachable."""
    from app.infrastructure.database import init_engine, init_session_factory

    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecretkey_min_32_characters_long_for_hs256",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        # Simulate broken engine on app.state
        broken_engine = init_engine("sqlite+aiosqlite:///non_existent_dir_123/unwritable.db")
        app.state.engine = broken_engine

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert "database" in data


def test_health_ready_endpoint_engine_uninitialized():
    """Readiness probe returns HTTP 503 when app.state.engine is None."""
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecretkey_min_32_characters_long_for_hs256",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        app.state.engine = None
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"

