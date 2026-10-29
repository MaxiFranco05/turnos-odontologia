from datetime import datetime, timedelta, timezone
import inspect
import pytest
from fastapi import HTTPException
from jose import JWTError

from app.domain.models.enums import RolUsuario
from app.infrastructure.config import Settings
from app.infrastructure.security import (
    LoginRateLimiter,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test_jwt_secret_key_for_hs256_signing_minimum_length",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_MINUTES=60,
    )


def test_security_functions_are_synchronous() -> None:
    """Hard Rule #3: pure CPU/in-memory security helpers must not be async def."""
    assert not inspect.iscoroutinefunction(hash_password)
    assert not inspect.iscoroutinefunction(verify_password)
    assert not inspect.iscoroutinefunction(create_access_token)
    assert not inspect.iscoroutinefunction(decode_access_token)
    assert not inspect.iscoroutinefunction(LoginRateLimiter.check_or_raise)


def test_password_hashing_and_verification() -> None:
    """Verifies bcrypt hashing generates salted hashes and validates matching/non-matching passwords."""
    plain = "ClaveSegura123!"
    hashed_1 = hash_password(plain)
    hashed_2 = hash_password(plain)

    assert hashed_1 != plain
    assert hashed_1.startswith("$2b$")
    # Salted hashes for identical input must differ
    assert hashed_1 != hashed_2

    assert verify_password(plain, hashed_1) is True
    assert verify_password(plain, hashed_2) is True
    assert verify_password("ClaveIncorrecta999!", hashed_1) is False


def test_create_and_decode_access_token_claims(test_settings: Settings) -> None:
    """Verifies JWT creation includes sub, rol, debe_cambiar_password, and exp claims."""
    before = int(datetime.now(timezone.utc).timestamp())
    token = create_access_token(
        user_id=42,
        rol=RolUsuario.PACIENTE,
        debe_cambiar_password=True,
        settings=test_settings,
    )
    after = int(datetime.now(timezone.utc).timestamp())

    payload = decode_access_token(token, test_settings)
    assert payload["sub"] == "42"
    assert payload["rol"] == "paciente"
    assert payload["debe_cambiar_password"] is True
    assert isinstance(payload["exp"], int)
    expected_min_exp = before + (test_settings.JWT_EXPIRE_MINUTES * 60)
    expected_max_exp = after + (test_settings.JWT_EXPIRE_MINUTES * 60)
    assert expected_min_exp <= payload["exp"] <= expected_max_exp


def test_decode_access_token_rejects_expired_and_tampered_tokens(test_settings: Settings) -> None:
    """Triangulation: expired tokens and tokens signed with a different secret raise JWTError."""
    expired_token = create_access_token(
        user_id=7,
        rol=RolUsuario.ODONTOLOGO,
        debe_cambiar_password=False,
        settings=test_settings,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(JWTError):
        decode_access_token(expired_token, test_settings)

    other_settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="completely_different_secret_key_that_must_fail",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_MINUTES=60,
    )
    valid_token = create_access_token(
        user_id=7,
        rol=RolUsuario.ODONTOLOGO,
        debe_cambiar_password=False,
        settings=test_settings,
    )
    with pytest.raises(JWTError):
        decode_access_token(valid_token, other_settings)


def test_login_rate_limiter_sliding_window() -> None:
    """Verifies 5 attempts in 60s succeed, 6th raises 429, other identifier is unaffected, and window expiry resets."""
    current_time = 1000.0
    limiter = LoginRateLimiter(max_requests=5, window_seconds=60.0, clock=lambda: current_time)

    # 5 attempts for identifier A from same IP succeed
    for _ in range(5):
        limiter.check_or_raise("192.168.1.10", "paciente.test@example.com")

    # 6th attempt within 60s for same (ip, identificador) raises 429 (even with case/whitespace difference)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_or_raise("192.168.1.10", "  PACIENTE.TEST@example.com ")
    assert exc_info.value.status_code == 429

    # Different identifier from same IP is NOT blocked
    limiter.check_or_raise("192.168.1.10", "SOC-1002")

    # Advance clock past 60s window -> identifier A is allowed again
    current_time += 60.1
    limiter.check_or_raise("192.168.1.10", "paciente.test@example.com")


@pytest.fixture
def auth_client(test_settings: Settings):
    """Provides a TestClient backed by a real SQLite async in-memory database with seeded synthetic users."""
    from starlette.testclient import TestClient

    from app.domain.models.base import Base
    from app.domain.models.usuario import Usuario
    from app.main import create_app

    app = create_app(settings=test_settings)

    with TestClient(app) as client:
        async def _seed() -> dict[str, int]:
            async with app.state.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with app.state.session_factory() as session:
                paciente = Usuario(
                    nombre="Paciente Sintético",
                    email="paciente.test@example.com",
                    nro_socio="SOC-1001",
                    password_hash=hash_password("PacientePass123!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=True,
                    perfil_completo=False,
                )
                recepcion = Usuario(
                    nombre="Recepción Sintética",
                    email="recepcion.test@example.com",
                    nro_socio=None,
                    password_hash=hash_password("RecepcionPass123!"),
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo = Usuario(
                    nombre="Odontólogo Sintético",
                    email="odontologo.test@example.com",
                    nro_socio="ODO-2001",
                    password_hash=hash_password("OdontologoPass123!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                session.add_all([paciente, recepcion, odontologo])
                await session.commit()
                await session.refresh(paciente)
                await session.refresh(recepcion)
                await session.refresh(odontologo)
                return {
                    "paciente_id": paciente.id,
                    "recepcion_id": recepcion.id,
                    "odontologo_id": odontologo.id,
                }

        assert client.portal is not None
        ids = client.portal.call(_seed)
        app.state.seeded_user_ids = ids
        yield client


def test_login_with_email_returns_jwt_and_claims(auth_client, test_settings: Settings) -> None:
    """Scenario: Successful login using email returns token, bearer type, rol, debe_cambiar_password, and valid claims."""
    response = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "recepcion.test@example.com",
            "password": "RecepcionPass123!",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["rol"] == "recepcion"
    assert body["debe_cambiar_password"] is False
    assert isinstance(body["access_token"], str)

    claims = decode_access_token(body["access_token"], test_settings)
    expected_id = str(auth_client.app.state.seeded_user_ids["recepcion_id"])
    assert claims["sub"] == expected_id
    assert claims["rol"] == "recepcion"
    assert claims["debe_cambiar_password"] is False
    assert "exp" in claims


def test_login_with_nro_socio_returns_jwt_and_claims(auth_client, test_settings: Settings) -> None:
    """Scenario: Successful login using membership number (nro_socio) returns token and debe_cambiar_password=True."""
    response = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "SOC-1001",
            "password": "PacientePass123!",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["rol"] == "paciente"
    assert body["debe_cambiar_password"] is True

    claims = decode_access_token(body["access_token"], test_settings)
    expected_id = str(auth_client.app.state.seeded_user_ids["paciente_id"])
    assert claims["sub"] == expected_id
    assert claims["rol"] == "paciente"
    assert claims["debe_cambiar_password"] is True


def test_login_generic_401_on_invalid_identifier_or_wrong_password(auth_client) -> None:
    """Scenario (RN-AU-01): Unknown identifier and wrong password both return HTTP 401 with identical generic detail."""
    resp_unknown = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "noexiste.test@example.com",
            "password": "CualquierPassword123!",
        },
    )
    resp_wrong_pw = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "paciente.test@example.com",
            "password": "PasswordIncorrecto999!",
        },
    )

    assert resp_unknown.status_code == 401
    assert resp_wrong_pw.status_code == 401
    assert resp_unknown.json() == {"detail": "Credenciales inválidas"}
    assert resp_wrong_pw.json() == {"detail": "Credenciales inválidas"}


def test_login_rejects_extra_fields_with_422(auth_client) -> None:
    """Scenario (Hard Rule #1): Login payload with undeclared fields is rejected with HTTP 422."""
    response = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "paciente.test@example.com",
            "password": "PacientePass123!",
            "campo_extra": "no_permitido",
        },
    )
    assert response.status_code == 422


def test_login_rate_limiting_5_per_60s_per_ip_and_identifier(auth_client) -> None:
    """Scenario: 6th request within 60s for same (ip, identificador) returns 429, while another identifier proceeds."""
    for _ in range(5):
        resp = auth_client.post(
            "/api/auth/login",
            json={
                "identificador": "SOC-1001",
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401

    # 6th attempt with same identifier (even with valid password) is rejected with 429
    sixth_resp = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "SOC-1001",
            "password": "PacientePass123!",
        },
    )
    assert sixth_resp.status_code == 429

    # Different identifier from the same IP is NOT blocked
    other_resp = auth_client.post(
        "/api/auth/login",
        json={
            "identificador": "recepcion.test@example.com",
            "password": "RecepcionPass123!",
        },
    )
    assert other_resp.status_code == 200


@pytest.fixture
def rbac_client(auth_client):
    """Attaches protected test endpoints using get_current_user and require_roles to auth_client.app."""
    from typing import Annotated

    from fastapi import Depends, Request

    from app.api.deps import get_current_user, require_roles
    from app.domain.models.usuario import Usuario

    app = auth_client.app

    @app.get("/api/test-protected/profile")
    def read_profile(
        request: Request,
        current_user: Annotated[Usuario, Depends(get_current_user)],
    ) -> dict[str, object]:
        state_user = getattr(request.state, "user", None)
        return {
            "id": current_user.id,
            "rol": current_user.rol.value,
            "state_user_matches": state_user is not None and state_user.id == current_user.id,
        }

    @app.get("/api/test-protected/clinical-staff")
    def read_clinical_staff(
        current_user: Annotated[
            Usuario,
            Depends(require_roles(RolUsuario.RECEPCION, RolUsuario.ODONTOLOGO)),
        ],
    ) -> dict[str, object]:
        return {
            "id": current_user.id,
            "rol": current_user.rol.value,
        }

    return auth_client


def test_deps_async_and_sync_conformance() -> None:
    """Hard Rule #3: get_current_user performs DB I/O (async def), require_roles checker is pure CPU (sync def)."""
    from app.api.deps import get_current_user, require_roles

    assert inspect.iscoroutinefunction(get_current_user)
    checker = require_roles(RolUsuario.PACIENTE)
    assert not inspect.iscoroutinefunction(checker)


def test_get_current_user_attaches_user_to_request_state(rbac_client) -> None:
    """Scenario: Valid Bearer token resolves Usuario and attaches it to request.state.user."""
    login_resp = rbac_client.post(
        "/api/auth/login",
        json={
            "identificador": "paciente.test@example.com",
            "password": "PacientePass123!",
        },
    )
    token = login_resp.json()["access_token"]

    resp = rbac_client.get(
        "/api/test-protected/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == rbac_client.app.state.seeded_user_ids["paciente_id"]
    assert data["rol"] == "paciente"
    assert data["state_user_matches"] is True


def test_get_current_user_rejects_missing_or_malformed_token_with_401(rbac_client) -> None:
    """Scenario: Missing Authorization header or malformed Bearer token returns HTTP 401."""
    resp_missing = rbac_client.get("/api/test-protected/profile")
    assert resp_missing.status_code == 401

    resp_malformed = rbac_client.get(
        "/api/test-protected/profile",
        headers={"Authorization": "Bearer token.invalido.malformado"},
    )
    assert resp_malformed.status_code == 401


def test_get_current_user_rejects_expired_token_with_401(
    rbac_client, test_settings: Settings
) -> None:
    """Scenario: Expired JWT token is rejected with HTTP 401."""
    paciente_id = rbac_client.app.state.seeded_user_ids["paciente_id"]
    expired_token = create_access_token(
        user_id=paciente_id,
        rol=RolUsuario.PACIENTE,
        debe_cambiar_password=True,
        settings=test_settings,
        expires_delta=timedelta(seconds=-30),
    )
    resp = rbac_client.get(
        "/api/test-protected/profile",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


def test_get_current_user_rejects_nonexistent_user_with_401(
    rbac_client, test_settings: Settings
) -> None:
    """Scenario: Valid signature token whose sub references a deleted/non-existent user returns HTTP 401."""
    ghost_token = create_access_token(
        user_id=999999,
        rol=RolUsuario.PACIENTE,
        debe_cambiar_password=False,
        settings=test_settings,
    )
    resp = rbac_client.get(
        "/api/test-protected/profile",
        headers={"Authorization": f"Bearer {ghost_token}"},
    )
    assert resp.status_code == 401


def test_require_roles_allows_permitted_roles_and_rejects_unpermitted_with_403(
    rbac_client,
) -> None:
    """Scenario (RN-AU-02, RN-GL-01): Permitted roles (recepcion, odontologo) get 200; paciente gets 403."""
    # Recepcion -> allowed (200)
    recep_login = rbac_client.post(
        "/api/auth/login",
        json={
            "identificador": "recepcion.test@example.com",
            "password": "RecepcionPass123!",
        },
    )
    recep_token = recep_login.json()["access_token"]
    resp_recep = rbac_client.get(
        "/api/test-protected/clinical-staff",
        headers={"Authorization": f"Bearer {recep_token}"},
    )
    assert resp_recep.status_code == 200
    assert resp_recep.json()["rol"] == "recepcion"

    # Odontologo -> allowed (200)
    odo_login = rbac_client.post(
        "/api/auth/login",
        json={
            "identificador": "odontologo.test@example.com",
            "password": "OdontologoPass123!",
        },
    )
    odo_token = odo_login.json()["access_token"]
    resp_odo = rbac_client.get(
        "/api/test-protected/clinical-staff",
        headers={"Authorization": f"Bearer {odo_token}"},
    )
    assert resp_odo.status_code == 200
    assert resp_odo.json()["rol"] == "odontologo"

    # Paciente -> forbidden (403)
    pac_login = rbac_client.post(
        "/api/auth/login",
        json={
            "identificador": "SOC-1001",
            "password": "PacientePass123!",
        },
    )
    pac_token = pac_login.json()["access_token"]
    resp_pac = rbac_client.get(
        "/api/test-protected/clinical-staff",
        headers={"Authorization": f"Bearer {pac_token}"},
    )
    assert resp_pac.status_code == 403


