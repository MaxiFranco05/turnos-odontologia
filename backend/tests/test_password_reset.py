import inspect
import pytest
from starlette.testclient import TestClient

from app.domain.models.base import Base
from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings
from app.infrastructure.security import (
    hash_password,
    validate_password_strength,
)
from app.main import create_app


@pytest.fixture
def reset_settings() -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test_jwt_secret_key_for_c04_password_reset_flow_hs256",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_MINUTES=60,
    )


def test_validate_password_strength_is_synchronous_and_enforces_rules() -> None:
    """Task 1.1: validate_password_strength is synchronous and enforces >=8 chars, >=1 uppercase, >=1 digit."""
    assert not inspect.iscoroutinefunction(validate_password_strength)

    # Valid passwords pass and return the password
    assert validate_password_strength("ClaveValida1") == "ClaveValida1"
    assert validate_password_strength("OtraPassword99!") == "OtraPassword99!"

    # Too short (< 8 chars)
    with pytest.raises(ValueError, match="8 caracteres"):
        validate_password_strength("Abc1234")

    # Missing uppercase letter
    with pytest.raises(ValueError, match="mayúscula"):
        validate_password_strength("solominusculas123")

    # Missing numeric digit
    with pytest.raises(ValueError, match="número"):
        validate_password_strength("SoloLetrasMayusculas")


@pytest.fixture
def reset_client(reset_settings: Settings):
    """Provides a TestClient backed by a real SQLite async in-memory DB with seeded synthetic users."""
    from typing import Annotated
    from fastapi import Depends

    from app.api.deps import require_password_changed, require_roles

    app = create_app(settings=reset_settings)

    @app.get("/api/test-c04/paciente-agenda")
    def read_paciente_agenda(
        current_user: Annotated[Usuario, Depends(require_roles(RolUsuario.PACIENTE))],
    ) -> dict[str, object]:
        return {"user_id": current_user.id, "rol": current_user.rol.value}

    @app.get("/api/test-c04/active-account")
    def read_active_account(
        current_user: Annotated[Usuario, Depends(require_password_changed)],
    ) -> dict[str, object]:
        return {"user_id": current_user.id}

    with TestClient(app) as client:
        async def _seed() -> dict[str, int]:
            async with app.state.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with app.state.session_factory() as session:
                # 1. Patient with email + nombre and debe_cambiar_password=True
                pac_temp = Usuario(
                    nombre="Paciente Temporal",
                    email="pac.temp@example.com",
                    nro_socio="SOC-3001",
                    password_hash=hash_password("TempPass123"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=True,
                    perfil_completo=False,
                )
                # 2. Patient with ONLY nro_socio (email=None) and debe_cambiar_password=True
                pac_sin_email = Usuario(
                    nombre="Paciente Sin Email",
                    email=None,
                    nro_socio="SOC-3002",
                    password_hash=hash_password("TempSocio123"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=True,
                    perfil_completo=False,
                )
                # 3. Patient who already changed password (debe_cambiar_password=False)
                pac_activo = Usuario(
                    nombre="Paciente Activo",
                    email="pac.activo@example.com",
                    nro_socio="SOC-3003",
                    password_hash=hash_password("ActivaPass123"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                session.add_all([pac_temp, pac_sin_email, pac_activo])
                await session.commit()
                await session.refresh(pac_temp)
                await session.refresh(pac_sin_email)
                await session.refresh(pac_activo)
                return {
                    "pac_temp_id": pac_temp.id,
                    "pac_sin_email_id": pac_sin_email.id,
                    "pac_activo_id": pac_activo.id,
                }

        assert client.portal is not None
        app.state.seeded_ids = client.portal.call(_seed)
        yield client


def test_require_roles_and_require_password_changed_block_pending_password_change(
    reset_client: TestClient,
) -> None:
    """Task 1.1 (US-010 CA-2): User with debe_cambiar_password=True is blocked with 403 'password_change_required'."""
    from app.api.deps import require_password_changed, require_roles

    assert not inspect.iscoroutinefunction(require_password_changed)
    assert not inspect.iscoroutinefunction(require_roles(RolUsuario.PACIENTE))

    login_resp = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.temp@example.com", "password": "TempPass123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Blocked on role-protected endpoint even though user has role PACIENTE
    resp_role = reset_client.get(
        "/api/test-c04/paciente-agenda",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_role.status_code == 403
    assert resp_role.json() == {"detail": "password_change_required"}

    # Blocked on require_password_changed endpoint
    resp_active = reset_client.get(
        "/api/test-c04/active-account",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_active.status_code == 403
    assert resp_active.json() == {"detail": "password_change_required"}


def test_first_time_password_change_success_and_unlocks_protected_routes(
    reset_client: TestClient, reset_settings: Settings
) -> None:
    """Task 2.1: First-time password change sets debe_cambiar_password=False, perfil_completo=True, and unlocks routes."""
    from app.infrastructure.security import decode_access_token

    login_resp = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.temp@example.com", "password": "TempPass123"},
    )
    assert login_resp.status_code == 200
    initial_token = login_resp.json()["access_token"]

    # Before password change, protected route returns 403 password_change_required
    blocked_resp = reset_client.get(
        "/api/test-c04/paciente-agenda",
        headers={"Authorization": f"Bearer {initial_token}"},
    )
    assert blocked_resp.status_code == 403
    assert blocked_resp.json() == {"detail": "password_change_required"}

    # Perform mandatory password change
    change_resp = reset_client.post(
        "/api/auth/cambiar-password",
        headers={"Authorization": f"Bearer {initial_token}"},
        json={
            "password_actual": "TempPass123",
            "password_nueva": "NuevaClaveSegura99",
        },
    )
    assert change_resp.status_code == 200
    body = change_resp.json()
    assert body["token_type"] == "bearer"
    assert body["rol"] == "paciente"
    assert body["debe_cambiar_password"] is False
    assert body["perfil_completo"] is True

    claims = decode_access_token(body["access_token"], reset_settings)
    assert claims["debe_cambiar_password"] is False

    # Protected route is now unlocked (200 OK)
    unlocked_resp = reset_client.get(
        "/api/test-c04/paciente-agenda",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert unlocked_resp.status_code == 200
    assert unlocked_resp.json()["rol"] == "paciente"

    # Old password no longer works; new password works
    old_login = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.temp@example.com", "password": "TempPass123"},
    )
    assert old_login.status_code == 401

    new_login = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.temp@example.com", "password": "NuevaClaveSegura99"},
    )
    assert new_login.status_code == 200
    assert new_login.json()["debe_cambiar_password"] is False
    assert new_login.json()["perfil_completo"] is True


def test_password_change_keeps_perfil_completo_false_when_email_absent_and_supports_noun_alias(
    reset_client: TestClient,
) -> None:
    """Task 2.1: Patient with email=None who changes password without providing email keeps perfil_completo=False."""
    login_resp = reset_client.post(
        "/api/auth/login",
        json={"identificador": "SOC-3002", "password": "TempSocio123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Using noun-based alias POST /api/auth/password without providing email
    change_resp = reset_client.post(
        "/api/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "password_actual": "TempSocio123",
            "password_nueva": "SocioNuevaPass88",
        },
    )
    assert change_resp.status_code == 200
    body = change_resp.json()
    assert body["debe_cambiar_password"] is False
    assert body["perfil_completo"] is False


def test_password_change_rejected_when_debe_cambiar_password_is_already_false(
    reset_client: TestClient,
) -> None:
    """Task 2.1: Calling POST /api/auth/cambiar-password when debe_cambiar_password=False returns 400."""
    login_resp = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.activo@example.com", "password": "ActivaPass123"},
    )
    token = login_resp.json()["access_token"]

    resp = reset_client.post(
        "/api/auth/cambiar-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "password_actual": "ActivaPass123",
            "password_nueva": "OtraClaveNueva99",
        },
    )
    assert resp.status_code == 400


def test_password_change_rejects_wrong_current_password_same_password_weak_password_extra_fields_and_duplicate_email(
    reset_client: TestClient,
) -> None:
    """Task 2.1: Rejects wrong password_actual (400), identical password_nueva (400), weak password (422), extra fields (422), and duplicate email (400)."""
    login_resp = reset_client.post(
        "/api/auth/login",
        json={"identificador": "pac.temp@example.com", "password": "TempPass123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Wrong password_actual -> 400
    resp_wrong_actual = reset_client.post(
        "/api/auth/cambiar-password",
        headers=headers,
        json={
            "password_actual": "Incorrecta123",
            "password_nueva": "NuevaClaveSegura99",
        },
    )
    assert resp_wrong_actual.status_code == 400
    assert resp_wrong_actual.json() == {"detail": "La contraseña actual es incorrecta"}

    # 2. Identical password_nueva == password_actual -> 400
    resp_same = reset_client.post(
        "/api/auth/cambiar-password",
        headers=headers,
        json={
            "password_actual": "TempPass123",
            "password_nueva": "TempPass123",
        },
    )
    assert resp_same.status_code == 400

    # 3. Weak password_nueva (short, no uppercase, no digit) -> 422
    for weak_pw in ("Abc12", "solominusculas123", "SoloLetrasMayusculas"):
        resp_weak = reset_client.post(
            "/api/auth/cambiar-password",
            headers=headers,
            json={
                "password_actual": "TempPass123",
                "password_nueva": weak_pw,
            },
        )
        assert resp_weak.status_code in (400, 422)

    # 4. Extra undeclared JSON field -> 422 (Hard Rule #1: extra='forbid')
    resp_extra = reset_client.post(
        "/api/auth/cambiar-password",
        headers=headers,
        json={
            "password_actual": "TempPass123",
            "password_nueva": "NuevaClaveSegura99",
            "hack_field": True,
        },
    )
    assert resp_extra.status_code == 422

    # 5. Duplicate email already belonging to another user -> 400
    resp_dup_email = reset_client.post(
        "/api/auth/cambiar-password",
        headers=headers,
        json={
            "password_actual": "TempPass123",
            "password_nueva": "NuevaClaveSegura99",
            "email": "pac.activo@example.com",
        },
    )
    assert resp_dup_email.status_code == 400

    # Verify debe_cambiar_password is STILL True after all rejected attempts
    still_blocked = reset_client.get("/api/test-c04/paciente-agenda", headers=headers)
    assert still_blocked.status_code == 403
    assert still_blocked.json() == {"detail": "password_change_required"}

