import datetime
from zoneinfo import ZoneInfo
import anyio
import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from app.api.agenda import (
    AgendaOdontologoResponse,
    AgendaPacienteResponse,
    AgendaTurnoDiaResponse,
)
from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings
from app.infrastructure.security import create_access_token, hash_password
from app.main import create_app

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


# =====================================================================
# Unit Validation: Schemas with extra="forbid" (Hard Rule #1 & BOPLA)
# =====================================================================


def test_agenda_response_schemas_forbid_extra_and_omit_sensitive_fields():
    """Verifies that response DTOs forbid extra attributes and omit passwords (BOPLA)."""
    pac = AgendaPacienteResponse(
        id=1,
        nombre="Paciente Sintético Uno",
        nro_socio="SOC-SINT-001",
        email="paciente1@example.com",
    )
    assert pac.nombre == "Paciente Sintético Uno"

    # Reject forbidden extra attributes on patient
    for forbidden_field in (
        {"password_hash": "$2b$12$secret"},
        {"debe_cambiar_password": False},
        {"rol": "paciente"},
    ):
        with pytest.raises(ValidationError):
            AgendaPacienteResponse(
                id=1,
                nombre="Paciente Sintético Uno",
                nro_socio="SOC-SINT-001",
                email="paciente1@example.com",
                **forbidden_field,
            )

    odo = AgendaOdontologoResponse(
        id=2,
        nombre="Dr. Odontólogo Sintético Uno",
        email="odontologo1@example.com",
    )
    assert odo.nombre == "Dr. Odontólogo Sintético Uno"

    # Reject forbidden extra attributes on dentist
    with pytest.raises(ValidationError):
        AgendaOdontologoResponse(
            id=2,
            nombre="Dr. Odontólogo Sintético Uno",
            email="odontologo1@example.com",
            password_hash="$2b$12$secret",
        )

    turno_item = AgendaTurnoDiaResponse(
        id=10,
        paciente_id=1,
        odontologo_id=2,
        inicio=datetime.datetime(2026, 11, 20, 9, 0, tzinfo=AR_TZ),
        fin=datetime.datetime(2026, 11, 20, 9, 30, tzinfo=AR_TZ),
        motivo="Consulta odontológica",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.ONLINE,
        paciente=pac,
        odontologo=odo,
    )
    assert turno_item.id == 10

    # Reject extra fields on appointment item
    with pytest.raises(ValidationError):
        AgendaTurnoDiaResponse(
            id=10,
            paciente_id=1,
            odontologo_id=2,
            inicio=datetime.datetime(2026, 11, 20, 9, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2026, 11, 20, 9, 30, tzinfo=AR_TZ),
            motivo="Consulta odontológica",
            estado=EstadoTurno.CONFIRMADO,
            origen=OrigenTurno.ONLINE,
            paciente=pac,
            odontologo=odo,
            extra_hack="unauthorized",
        )


# =====================================================================
# Integration Fixture: Real SQLite Database without Mocks (Hard Rule #7)
# =====================================================================


@pytest.fixture
def reception_agenda_client_and_context():
    """Sets up a real in-memory SQLite database and authenticated test clients."""
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecret_jwt_key_at_least_32_characters_long!",
        TIMEZONE="America/Argentina/Buenos_Aires",
        _env_file=None,
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        async def _seed():
            async with app.state.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with app.state.session_factory() as session:
                recepcion = Usuario(
                    nombre="Recepción Central (Ficticia)",
                    email="recepcion.ficticia@example.com",
                    nro_socio=None,
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_ana = Usuario(
                    nombre="Dra. Ana López (Ficticia)",
                    email="ana.lopez.ficticia@example.com",
                    nro_socio="ODO-FICT-801",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_carlos = Usuario(
                    nombre="Dr. Carlos Ruiz (Ficticio)",
                    email="carlos.ruiz.ficticio@example.com",
                    nro_socio="ODO-FICT-802",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_matias = Usuario(
                    nombre="Matías Rossi (Ficticio)",
                    email="matias.rossi.ficticio@example.com",
                    nro_socio="SOC-FICT-801",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_valeria = Usuario(
                    nombre="Valeria Vega (Ficticia)",
                    email="valeria.vega.ficticia@example.com",
                    nro_socio="SOC-FICT-802",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )

                session.add_all([
                    recepcion,
                    odontologo_ana,
                    odontologo_carlos,
                    paciente_matias,
                    paciente_valeria,
                ])
                await session.commit()
                for u in (
                    recepcion,
                    odontologo_ana,
                    odontologo_carlos,
                    paciente_matias,
                    paciente_valeria,
                ):
                    await session.refresh(u)

                # Seed appointments for target date: 2026-11-20
                # 1. 09:00 - 09:30 Dra. Ana, Matías (confirmado, online)
                t1 = Turno(
                    paciente_id=paciente_matias.id,
                    odontologo_id=odontologo_ana.id,
                    inicio=datetime.datetime(2026, 11, 20, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 11, 20, 9, 30, tzinfo=AR_TZ),
                    motivo="Limpieza y diagnóstico",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )
                # 2. 10:00 - 10:30 Dr. Carlos, Valeria (cancelado, online - US-005 tracking)
                t2 = Turno(
                    paciente_id=paciente_valeria.id,
                    odontologo_id=odontologo_carlos.id,
                    inicio=datetime.datetime(2026, 11, 20, 10, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 11, 20, 10, 30, tzinfo=AR_TZ),
                    motivo="Consulta urgencia cancelada",
                    estado=EstadoTurno.CANCELADO,
                    origen=OrigenTurno.ONLINE,
                )
                # 3. 11:00 - 11:30 Dra. Ana, Valeria (solicitado, manual)
                t3 = Turno(
                    paciente_id=paciente_valeria.id,
                    odontologo_id=odontologo_ana.id,
                    inicio=datetime.datetime(2026, 11, 20, 11, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 11, 20, 11, 30, tzinfo=AR_TZ),
                    motivo="Revisión de ortodoncia",
                    estado=EstadoTurno.SOLICITADO,
                    origen=OrigenTurno.MANUAL,
                )
                # 4. Turno on adjacent previous day: 2026-11-19 23:30 (must be excluded)
                t_prev = Turno(
                    paciente_id=paciente_matias.id,
                    odontologo_id=odontologo_ana.id,
                    inicio=datetime.datetime(2026, 11, 19, 23, 30, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 11, 19, 23, 59, tzinfo=AR_TZ),
                    motivo="Turno previo",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )
                # 5. Turno on next day: 2026-11-21 09:00 (must be excluded)
                t_next = Turno(
                    paciente_id=paciente_matias.id,
                    odontologo_id=odontologo_ana.id,
                    inicio=datetime.datetime(2026, 11, 21, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 11, 21, 9, 30, tzinfo=AR_TZ),
                    motivo="Turno posterior",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )

                session.add_all([t1, t2, t3, t_prev, t_next])
                await session.commit()

                return {
                    "recepcion": recepcion,
                    "odontologo_ana": odontologo_ana,
                    "odontologo_carlos": odontologo_carlos,
                    "paciente_matias": paciente_matias,
                    "paciente_valeria": paciente_valeria,
                    "turnos": [t1, t2, t3],
                }

        context = anyio.run(_seed)
        tokens = {
            key: create_access_token(
                user_id=user.id,
                rol=user.rol,
                debe_cambiar_password=user.debe_cambiar_password,
                settings=settings,
            )
            for key, user in context.items()
            if isinstance(user, Usuario)
        }
        yield client, app, context, tokens


# =====================================================================
# Scenarios 1 & 7 & 9: All Dentists Daily Retrieval, US-005, BOPLA
# =====================================================================


def test_reception_agenda_all_dentists_happy_path_and_bopla(
    reception_agenda_client_and_context,
):
    """Scenario 1, 7, 9: Reception queries full clinic agenda for date, verifies ordering and credential protection."""
    client, _app, context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}

    res = client.get("/api/agenda/dia?fecha=2026-11-20", headers=headers)
    assert res.status_code == 200
    items = res.json()

    # Exactly 3 appointments on 2026-11-20
    assert len(items) == 3

    # Ordered ascending by inicio
    inicios = [datetime.datetime.fromisoformat(item["inicio"]) for item in items]
    assert inicios == sorted(inicios)

    # Item 1: Dra. Ana (09:00)
    assert items[0]["odontologo_id"] == context["odontologo_ana"].id
    assert items[0]["paciente_id"] == context["paciente_matias"].id
    assert items[0]["estado"] == "confirmado"
    assert items[0]["origen"] == "online"
    assert items[0]["paciente"]["nombre"] == "Matías Rossi (Ficticio)"
    assert items[0]["odontologo"]["nombre"] == "Dra. Ana López (Ficticia)"

    # Item 2: Dr. Carlos (10:00) - Cancelled appointment included with online origin (US-005 CA-1/CA-2)
    assert items[1]["odontologo_id"] == context["odontologo_carlos"].id
    assert items[1]["estado"] == "cancelado"
    assert items[1]["origen"] == "online"

    # Item 3: Dra. Ana (11:00)
    assert items[2]["odontologo_id"] == context["odontologo_ana"].id
    assert items[2]["estado"] == "solicitado"
    assert items[2]["origen"] == "manual"

    # BOPLA Protection: Verify that neither patient nor dentist exposes password hashes or secret flags
    for item in items:
        assert "password_hash" not in item["paciente"]
        assert "debe_cambiar_password" not in item["paciente"]
        assert "password_hash" not in item["odontologo"]
        assert "debe_cambiar_password" not in item["odontologo"]


# =====================================================================
# Scenario 2: Filter Daily Agenda by Specific Dentist
# =====================================================================


def test_reception_agenda_filter_by_dentist(reception_agenda_client_and_context):
    """Scenario 2: Reception filters daily agenda by dentist ID."""
    client, _app, context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}

    ana_id = context["odontologo_ana"].id
    carlos_id = context["odontologo_carlos"].id

    # Filter for Dra. Ana -> exactly 2 appointments (09:00 and 11:00)
    res_ana = client.get(
        f"/api/agenda/dia?fecha=2026-11-20&odontologo_id={ana_id}",
        headers=headers,
    )
    assert res_ana.status_code == 200
    items_ana = res_ana.json()
    assert len(items_ana) == 2
    assert all(item["odontologo_id"] == ana_id for item in items_ana)

    # Filter for Dr. Carlos -> exactly 1 appointment (10:00)
    res_carlos = client.get(
        f"/api/agenda/dia?fecha=2026-11-20&odontologo_id={carlos_id}",
        headers=headers,
    )
    assert res_carlos.status_code == 200
    items_carlos = res_carlos.json()
    assert len(items_carlos) == 1
    assert items_carlos[0]["odontologo_id"] == carlos_id


# =====================================================================
# Scenario 3: Unauthorized Access by Non-Reception Users (RN-GL-01)
# =====================================================================


def test_reception_agenda_rbac_forbidden_for_other_roles(
    reception_agenda_client_and_context,
):
    """Scenario 3 (RN-GL-01 & RN-AU-02): Patient and Dentist roles are rejected with 403 Forbidden."""
    client, _app, _context, tokens = reception_agenda_client_and_context

    # 1. Patient attempt -> 403 Forbidden
    res_pac = client.get(
        "/api/agenda/dia?fecha=2026-11-20",
        headers={"Authorization": f"Bearer {tokens['paciente_matias']}"},
    )
    assert res_pac.status_code == 403

    # 2. Dentist attempt -> 403 Forbidden
    res_odo = client.get(
        "/api/agenda/dia?fecha=2026-11-20",
        headers={"Authorization": f"Bearer {tokens['odontologo_ana']}"},
    )
    assert res_odo.status_code == 403

    # 3. Unauthenticated attempt -> 401 Unauthorized
    res_unauth = client.get("/api/agenda/dia?fecha=2026-11-20")
    assert res_unauth.status_code == 401


# =====================================================================
# Scenario 4: Missing Required Date Parameter
# =====================================================================


def test_reception_agenda_missing_fecha_query_parameter(
    reception_agenda_client_and_context,
):
    """Scenario 4: Missing required query parameter 'fecha' returns 422 Unprocessable Entity."""
    client, _app, _context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}

    res = client.get("/api/agenda/dia", headers=headers)
    assert res.status_code == 422


# =====================================================================
# Scenario 5 & 6: CB-06 Dentist Validation (404 / 422)
# =====================================================================


def test_reception_agenda_cb06_nonexistent_dentist_returns_404(
    reception_agenda_client_and_context,
):
    """Scenario 5 (CB-06): Querying with nonexistent odontologo_id returns 404 Not Found."""
    client, _app, _context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}

    res = client.get(
        "/api/agenda/dia?fecha=2026-11-20&odontologo_id=999999",
        headers=headers,
    )
    assert res.status_code == 404
    assert "no encontrado" in res.json()["detail"].lower()


def test_reception_agenda_cb06_non_dentist_user_returns_422(
    reception_agenda_client_and_context,
):
    """Scenario 6 (CB-06): Querying with odontologo_id belonging to a patient returns 422 Unprocessable Entity."""
    client, _app, context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}
    patient_id = context["paciente_matias"].id

    res = client.get(
        f"/api/agenda/dia?fecha=2026-11-20&odontologo_id={patient_id}",
        headers=headers,
    )
    assert res.status_code == 422
    assert "rol de odontólogo" in res.json()["detail"].lower()


# =====================================================================
# Scenario 8: Empty Agenda on Date with No Appointments
# =====================================================================


def test_reception_agenda_empty_day_returns_200_empty_list(
    reception_agenda_client_and_context,
):
    """Scenario 8: Querying a date without appointments returns 200 OK with empty list []."""
    client, _app, _context, tokens = reception_agenda_client_and_context
    headers = {"Authorization": f"Bearer {tokens['recepcion']}"}

    res = client.get("/api/agenda/dia?fecha=2029-01-01", headers=headers)
    assert res.status_code == 200
    assert res.json() == []
