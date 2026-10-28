import pytest
from pydantic import ValidationError


def test_settings_load_valid_values(monkeypatch):
    """Happy path: valid configuration values are loaded correctly."""
    from app.infrastructure.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/turnos_db")
    monkeypatch.setenv("JWT_SECRET", "supersecretkey_min_32_characters_long_for_hs256")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "45")
    monkeypatch.setenv("CANCEL_MIN_HOURS", "48")
    monkeypatch.setenv("TIMEZONE", "America/Argentina/Buenos_Aires")

    settings = Settings()

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/turnos_db"
    assert settings.JWT_SECRET == "supersecretkey_min_32_characters_long_for_hs256"
    assert settings.JWT_EXPIRE_MINUTES == 45
    assert settings.CANCEL_MIN_HOURS == 48
    assert settings.TIMEZONE == "America/Argentina/Buenos_Aires"


def test_settings_missing_required_database_url(monkeypatch):
    """Fails when mandatory DATABASE_URL is missing."""
    from app.infrastructure.config import Settings

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("JWT_SECRET", "supersecretkey_min_32_characters_long_for_hs256")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    errors = exc_info.value.errors()
    field_names = [e["loc"][0] for e in errors]
    assert "DATABASE_URL" in field_names


def test_settings_rejects_extra_fields(monkeypatch):
    """Hard Rule #1: Pydantic schemas must enforce extra='forbid'."""
    from app.infrastructure.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/turnos_db")
    monkeypatch.setenv("JWT_SECRET", "supersecretkey_min_32_characters_long_for_hs256")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, EXTRA_UNDECLARED_PARAM="should_fail")

    errors = exc_info.value.errors()
    assert any("extra_forbidden" in e["type"] for e in errors)


def test_settings_async_driver_coercion(monkeypatch):
    """Normalizes plain postgresql:// to postgresql+asyncpg://."""
    from app.infrastructure.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/turnos_db")
    monkeypatch.setenv("JWT_SECRET", "supersecretkey_min_32_characters_long_for_hs256")

    settings = Settings(_env_file=None)
    assert settings.async_database_url == "postgresql+asyncpg://user:pass@localhost:5432/turnos_db"


def test_settings_defaults(monkeypatch):
    """Verifies default values for APP_ENV, DEBUG, and PORT."""
    from app.infrastructure.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setenv("JWT_SECRET", "supersecretkey_min_32_characters_long_for_hs256")

    settings = Settings(_env_file=None)
    assert settings.APP_ENV == "development"
    assert settings.DEBUG is False
    assert settings.PORT == 8000
    assert settings.CANCEL_MIN_HOURS == 24

