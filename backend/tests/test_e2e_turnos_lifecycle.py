import datetime
from zoneinfo import ZoneInfo
import anyio
import pytest
from starlette.testclient import TestClient

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings
from app.infrastructure.security import create_access_token, hash_password
from app.main import create_app


def _get_next_weekday(start_date: datetime.date, target_weekday: int) -> datetime.date:
    """Finds next target weekday (0=Monday, ..., 6=Sunday) strictly in the future."""
    days_ahead = (target_weekday - start_date.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + datetime.timedelta(days=days_ahead)


@pytest.fixture
def e2e_context():
    """Sets up an isolated database with synthetic users, templates, and JWT tokens."""
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecret_jwt_key_at_least_32_characters_long_for_e2e_testing!",
        TIMEZONE="America/Argentina/Buenos_Aires",
        CANCEL_MIN_HOURS=24,
        _env_file=None,
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        async def _seed():
            async with app.state.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with app.state.session_factory() as session:
                # Fictitious synthetic users (Hard Rule #12)
                paciente_uno = Usuario(
                    nombre="Paciente Ficticio Uno",
                    email="paciente1.ficticio@example.com",
                    nro_socio="SOC-E2E-001",
                    password_hash=hash_password("ClavePaciente1!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_dos = Usuario(
                    nombre="Paciente Ficticio Dos",
                    email="paciente2.ficticio@example.com",
                    nro_socio="SOC-E2E-002",
                    password_hash=hash_password("ClavePaciente2!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                recepcionista = Usuario(
                    nombre="Recepción Ficticia Central",
                    email="recepcion.ficticia@example.com",
                    nro_socio=None,
                    password_hash=hash_password("ClaveRecep1!"),
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_uno = Usuario(
                    nombre="Dr. Odontólogo Ficticio Uno",
                    email="dr.ficticio1@example.com",
                    nro_socio="ODO-E2E-101",
                    password_hash=hash_password("ClaveDentist1!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_dos = Usuario(
                    nombre="Dra. Odontóloga Ficticia Dos",
                    email="dr.ficticio2@example.com",
                    nro_socio="ODO-E2E-102",
                    password_hash=hash_password("ClaveDentist2!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )

                session.add_all([paciente_uno, paciente_dos, recepcionista, odontologo_uno, odontologo_dos])
                await session.commit()
                for u in (paciente_uno, paciente_dos, recepcionista, odontologo_uno, odontologo_dos):
                    await session.refresh(u)

                # Template for Odontologo Uno: Monday (0) from 09:00 to 12:00, 30 min slots
                tpl_lunes = PlantillaDisponibilidad(
                    odontologo_id=odontologo_uno.id,
                    dia_semana=0,
                    hora_inicio=datetime.time(9, 0),
                    hora_fin=datetime.time(12, 0),
                    duracion_slot_minutos=30,
                    prestacion="Consulta general",
                )
                session.add(tpl_lunes)
                await session.commit()
                await session.refresh(tpl_lunes)

                return {
                    "paciente_uno": paciente_uno,
                    "paciente_dos": paciente_dos,
                    "recepcionista": recepcionista,
                    "odontologo_uno": odontologo_uno,
                    "odontologo_dos": odontologo_dos,
                    "template_lunes": tpl_lunes,
                    "settings": settings,
                }

        ctx = anyio.run(_seed)

        # Generate tokens
        def _get_headers(user: Usuario):
            token = create_access_token(
                user_id=user.id,
                rol=user.rol,
                debe_cambiar_password=user.debe_cambiar_password,
                settings=settings,
            )
            return {"Authorization": f"Bearer {token}"}

        yield {
            "client": client,
            "headers_paciente_1": _get_headers(ctx["paciente_uno"]),
            "headers_paciente_2": _get_headers(ctx["paciente_dos"]),
            "headers_recepcion": _get_headers(ctx["recepcionista"]),
            "headers_odontologo_1": _get_headers(ctx["odontologo_uno"]),
            "headers_odontologo_2": _get_headers(ctx["odontologo_dos"]),
            "odontologo_uno": ctx["odontologo_uno"],
            "odontologo_dos": ctx["odontologo_dos"],
            "settings": settings,
            "app": app,
        }


def test_e2e_complete_appointment_lifecycle_across_all_roles(e2e_context):
    """E2E Scenario: Happy path appointment lifecycle across all roles.
    
    1. Paciente 1 logs in & requests appointment in free slot -> solicitado (201).
    2. Recepción logs in, reviews daily agenda -> confirms appointment -> confirmado (200).
    3. Assigned Odontólogo 1 logs in, reviews his agenda -> marks attendance -> presente (200).
    4. Paciente attempts to cancel afterwards -> rejected with 409 Conflict.
    """
    client = e2e_context["client"]
    dentist_id = e2e_context["odontologo_uno"].id
    zone = ZoneInfo(e2e_context["settings"].TIMEZONE)
    today = datetime.datetime.now(zone).date()
    target_date = _get_next_weekday(today, 0)  # Next Monday

    slot_start = datetime.datetime.combine(target_date, datetime.time(9, 0), tzinfo=zone)
    slot_end = datetime.datetime.combine(target_date, datetime.time(9, 30), tzinfo=zone)

    # Step 1: Paciente 1 requests slot 09:00 - 09:30
    req_payload = {
        "odontologo_id": dentist_id,
        "inicio": slot_start.isoformat(),
        "fin": slot_end.isoformat(),
        "motivo": "Revisión semestral preventiva",
    }
    res_solicitud = client.post("/api/turnos", json=req_payload, headers=e2e_context["headers_paciente_1"])
    assert res_solicitud.status_code == 201, res_solicitud.text
    turno_data = res_solicitud.json()
    turno_id = turno_data["id"]
    assert turno_data["estado"] == "solicitado"
    assert turno_data["origen"] == "online"

    # Step 2: Recepción inspects daily agenda
    res_agenda = client.get(f"/api/agenda/dia?fecha={target_date}", headers=e2e_context["headers_recepcion"])
    assert res_agenda.status_code == 200, res_agenda.text
    agenda_turnos = res_agenda.json()
    assert any(t["id"] == turno_id and t["estado"] == "solicitado" for t in agenda_turnos)

    # Step 3: Recepción confirms the appointment
    patch_conf = {"estado": "confirmado"}
    res_conf = client.patch(f"/api/turnos/{turno_id}", json=patch_conf, headers=e2e_context["headers_recepcion"])
    assert res_conf.status_code == 200, res_conf.text
    assert res_conf.json()["estado"] == "confirmado"

    # Step 4: Assigned Odontólogo 1 checks his assigned agenda
    res_mis_turnos = client.get(f"/api/mis-turnos?fecha={target_date}", headers=e2e_context["headers_odontologo_1"])
    assert res_mis_turnos.status_code == 200, res_mis_turnos.text
    turnos_dentist = res_mis_turnos.json()
    assert any(t["id"] == turno_id and t["estado"] == "confirmado" for t in turnos_dentist)

    # Step 5: Odontólogo 1 marks attendance (presente)
    patch_pres = {"estado": "presente"}
    res_pres = client.patch(f"/api/turnos/{turno_id}", json=patch_pres, headers=e2e_context["headers_odontologo_1"])
    assert res_pres.status_code == 200, res_pres.text
    assert res_pres.json()["estado"] == "presente"

    # Step 6: Paciente attempts to cancel already completed appointment -> 409 Conflict
    patch_canc = {"estado": "cancelado"}
    res_canc = client.patch(f"/api/turnos/{turno_id}", json=patch_canc, headers=e2e_context["headers_paciente_1"])
    assert res_canc.status_code == 409, (
        f"Expected 409 Conflict on cancelling an attended appointment, got {res_canc.status_code}"
    )


def test_e2e_anti_overlap_concurrent_request_rejected(e2e_context):
    """E2E Scenario: Attempted overlapping booking rejected with 409 Conflict (Hard Rule #13, RN-AG-01)."""
    client = e2e_context["client"]
    dentist_id = e2e_context["odontologo_uno"].id
    zone = ZoneInfo(e2e_context["settings"].TIMEZONE)
    today = datetime.datetime.now(zone).date()
    target_date = _get_next_weekday(today, 0)

    slot_start = datetime.datetime.combine(target_date, datetime.time(9, 30), tzinfo=zone)
    slot_end = datetime.datetime.combine(target_date, datetime.time(10, 0), tzinfo=zone)

    # Paciente 1 takes slot 09:30 - 10:00
    payload = {
        "odontologo_id": dentist_id,
        "inicio": slot_start.isoformat(),
        "fin": slot_end.isoformat(),
        "motivo": "Limpieza dental",
    }
    res_1 = client.post("/api/turnos", json=payload, headers=e2e_context["headers_paciente_1"])
    assert res_1.status_code == 201, res_1.text

    # Paciente 2 attempts to take the exact same slot for the same dentist
    res_2 = client.post("/api/turnos", json=payload, headers=e2e_context["headers_paciente_2"])
    assert res_2.status_code == 409, f"Expected 409 Conflict for overlapping slot, got {res_2.status_code}"
    assert "RN-AG-01" in res_2.text or "ocupado" in res_2.text or "solape" in res_2.text.lower()


def test_e2e_early_cancellation_releases_availability_slot(e2e_context):
    """E2E Scenario: Early patient cancellation (>24h) releases slot back to availability (RN-TU-05, RN-AG-02)."""
    client = e2e_context["client"]
    dentist_id = e2e_context["odontologo_uno"].id
    zone = ZoneInfo(e2e_context["settings"].TIMEZONE)
    today = datetime.datetime.now(zone).date()
    target_date = _get_next_weekday(today, 0)

    slot_start = datetime.datetime.combine(target_date, datetime.time(10, 0), tzinfo=zone)
    slot_end = datetime.datetime.combine(target_date, datetime.time(10, 30), tzinfo=zone)

    # Step 1: Paciente 1 takes slot 10:00 - 10:30
    payload = {
        "odontologo_id": dentist_id,
        "inicio": slot_start.isoformat(),
        "fin": slot_end.isoformat(),
        "motivo": "Consulta ortodoncia",
    }
    res_post = client.post("/api/turnos", json=payload, headers=e2e_context["headers_paciente_1"])
    assert res_post.status_code == 201, res_post.text
    turno_id = res_post.json()["id"]

    # Step 2: Query availability: slot 10:00 - 10:30 must NOT be in available starts
    res_disp1 = client.get(
        f"/api/disponibilidad?fecha={target_date}&odontologo_id={dentist_id}",
        headers=e2e_context["headers_paciente_1"],
    )
    assert res_disp1.status_code == 200, res_disp1.text
    free_times_1 = [
        datetime.datetime.fromisoformat(s["inicio"]).astimezone(zone).time()
        for s in res_disp1.json()
    ]
    assert datetime.time(10, 0) not in free_times_1, "Slot 10:00 must be marked as not available while appointment is active"

    # Step 3: Paciente cancels appointment (>24h in advance)
    res_canc = client.patch(
        f"/api/turnos/{turno_id}",
        json={"estado": "cancelado"},
        headers=e2e_context["headers_paciente_1"],
    )
    assert res_canc.status_code == 200, res_canc.text
    assert res_canc.json()["estado"] == "cancelado"

    # Step 4: Query availability again: slot 10:00 - 10:30 must be freed and available
    res_disp2 = client.get(
        f"/api/disponibilidad?fecha={target_date}&odontologo_id={dentist_id}",
        headers=e2e_context["headers_paciente_1"],
    )
    assert res_disp2.status_code == 200, res_disp2.text
    free_times_2 = [
        datetime.datetime.fromisoformat(s["inicio"]).astimezone(zone).time()
        for s in res_disp2.json()
    ]
    assert datetime.time(10, 0) in free_times_2, "Slot 10:00 must be restored to available after cancellation"


def test_e2e_late_cancellation_within_minimum_window_rejected(e2e_context):
    """E2E Scenario: Late patient cancellation within minimum window (<24h) rejected with 422 (RN-TU-05)."""
    client = e2e_context["client"]
    app = e2e_context["app"]
    zone = ZoneInfo(e2e_context["settings"].TIMEZONE)
    now_local = datetime.datetime.now(zone)

    # Insert a confirmed appointment starting in 2 hours (<24h)
    start_time = now_local + datetime.timedelta(hours=2)
    end_time = start_time + datetime.timedelta(minutes=30)

    async def _insert_near_turno():
        async with app.state.session_factory() as session:
            near_turno = Turno(
                paciente_id=1,  # Paciente Uno
                odontologo_id=e2e_context["odontologo_uno"].id,
                inicio=start_time.replace(tzinfo=None),
                fin=end_time.replace(tzinfo=None),
                motivo="Urgencia próxima",
                estado=EstadoTurno.CONFIRMADO,
                origen=OrigenTurno.ONLINE,
            )
            session.add(near_turno)
            await session.commit()
            await session.refresh(near_turno)
            return near_turno.id

    turno_id = anyio.run(_insert_near_turno)

    # Patient attempts to cancel within the 24h anticipation window
    res_canc = client.patch(
        f"/api/turnos/{turno_id}",
        json={"estado": "cancelado"},
        headers=e2e_context["headers_paciente_1"],
    )
    assert res_canc.status_code == 422, f"Expected 422 Unprocessable Entity for late cancellation, got {res_canc.status_code}"
    assert "anticipación" in res_canc.text.lower() or "rn-tu-05" in res_canc.text.lower()


def test_e2e_cross_dentist_attendance_rejected_403(e2e_context):
    """E2E Scenario: Cross-dentist attendance mutation rejected with 403 Forbidden (RN-AU-02, RN-GL-01)."""
    client = e2e_context["client"]
    dentist_id = e2e_context["odontologo_uno"].id
    zone = ZoneInfo(e2e_context["settings"].TIMEZONE)
    today = datetime.datetime.now(zone).date()
    target_date = _get_next_weekday(today, 0)

    slot_start = datetime.datetime.combine(target_date, datetime.time(10, 30), tzinfo=zone)
    slot_end = datetime.datetime.combine(target_date, datetime.time(11, 0), tzinfo=zone)

    # Paciente requests slot 10:30 - 11:00 for Odontologo Uno
    payload = {
        "odontologo_id": dentist_id,
        "inicio": slot_start.isoformat(),
        "fin": slot_end.isoformat(),
        "motivo": "Consulta para Odontólogo Uno",
    }
    res_post = client.post("/api/turnos", json=payload, headers=e2e_context["headers_paciente_1"])
    assert res_post.status_code == 201, res_post.text
    turno_id = res_post.json()["id"]

    # Recepción confirms
    res_conf = client.patch(
        f"/api/turnos/{turno_id}",
        json={"estado": "confirmado"},
        headers=e2e_context["headers_recepcion"],
    )
    assert res_conf.status_code == 200, res_conf.text

    # Odontólogo Dos (different dentist) attempts to mark presente on Odontólogo Uno's appointment
    res_cross = client.patch(
        f"/api/turnos/{turno_id}",
        json={"estado": "presente"},
        headers=e2e_context["headers_odontologo_2"],
    )
    assert res_cross.status_code == 403, (
        f"Expected 403 Forbidden for cross-dentist state mutation, got {res_cross.status_code}"
    )
