import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from app.api.odontologos import OdontologoPublicResponse
from app.domain.models.base import Base
from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.database import init_engine, init_session_factory
from app.main import create_app


def test_odontologo_public_response_schema_strictness():
    """Hard Rule #1: OdontologoPublicResponse schema strictly rejects undeclared extra fields."""
    with pytest.raises(ValidationError):
        OdontologoPublicResponse(
            id=1,
            nombre="Dr. Lucas",
            undeclared_field="illegal",
        )

    valid = OdontologoPublicResponse(
        id=2,
        nombre="Dra. Sofía Martín",
        email="sofia@clinica.com",
        nro_socio="ODO-001",
        especialidad="Odontología General y Prevención",
    )
    assert valid.id == 2
    assert valid.nombre == "Dra. Sofía Martín"
    assert valid.especialidad == "Odontología General y Prevención"


@pytest.mark.asyncio
async def test_get_odontologos_endpoint(monkeypatch):
    """GET /api/odontologos returns only users with rol == ODONTOLOGO, omitting passwords/secrets."""
    from app.infrastructure.config import Settings
    test_settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test-secret-32-chars-long-minimum!",
        APP_ENV="testing",
    )
    app = create_app(settings=test_settings)

    with TestClient(app) as client:
        async with app.state.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with app.state.session_factory() as session:
            # 1 Recepcion
            session.add(
                Usuario(
                    nombre="Camila Recepción",
                    email="recepcion@clinica.com",
                    password_hash="dummy_hash_1",
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
            )
            # 2 Odontologos
            session.add(
                Usuario(
                    nombre="Dra. Sofía Martín (Ficticia)",
                    email="sofia.martin@turnosodontologia.com",
                    nro_socio="ODO-001",
                    password_hash="dummy_hash_2",
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
            )
            session.add(
                Usuario(
                    nombre="Dr. Lucas García (Ficticio)",
                    email="lucas.garcia@turnosodontologia.com",
                    nro_socio="ODO-002",
                    password_hash="dummy_hash_3",
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
            )
            # 1 Paciente
            session.add(
                Usuario(
                    nombre="Lucía Gómez",
                    email="lucia.gomez@gmail.com",
                    password_hash="dummy_hash_4",
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
            )
            await session.commit()

        res = client.get("/api/odontologos")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2

        # Verify only odontologos are present and (Ficticia)/(Ficticio) is cleanly stripped
        names = [d["nombre"] for d in data]
        assert "Dra. Sofía Martín" in names
        assert "Dr. Lucas García" in names
        assert "Camila Recepción" not in names
        assert "Lucía Gómez" not in names

        # Verify specialties are mapped
        sofia = next(d for d in data if d["nombre"] == "Dra. Sofía Martín")
        assert sofia["especialidad"] == "Odontología General y Prevención"
        lucas = next(d for d in data if d["nombre"] == "Dr. Lucas García")
        assert lucas["especialidad"] == "Ortodoncia y Prótesis"

        # Verify no sensitive fields leaked
        for d in data:
            assert "password" not in d
            assert "password_hash" not in d
            assert "debe_cambiar_password" not in d
