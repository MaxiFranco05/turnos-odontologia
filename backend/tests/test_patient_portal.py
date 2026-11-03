import datetime
import inspect
from zoneinfo import ZoneInfo

import pytest

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


# =====================================================================
# Task 1.1: Pure Synchronous get_clinic_date_range_bounds & N+1 Prevention
# =====================================================================


def test_get_clinic_date_range_bounds_is_pure_synchronous_function():
    """Task 1.1 (Hard Rule #3): get_clinic_date_range_bounds must be a pure synchronous def function."""
    from app.application.turnos import get_clinic_date_range_bounds

    assert inspect.isfunction(get_clinic_date_range_bounds)
    assert not inspect.iscoroutinefunction(get_clinic_date_range_bounds)


def test_get_clinic_date_range_bounds_unbounded_and_partial_ranges():
    """Task 1.1: Computes half-open clinic date range bounds [start, end) in America/Argentina/Buenos_Aires."""
    from app.application.turnos import get_clinic_date_range_bounds

    # 1. Both omitted -> wide clinic bounds [1970-01-01 00:00:00, 2100-01-02 00:00:00)
    start_all, end_all = get_clinic_date_range_bounds()
    assert start_all == datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=AR_TZ)
    assert end_all == datetime.datetime(2100, 1, 2, 0, 0, 0, tzinfo=AR_TZ)

    # 2. Only fecha_desde provided
    start_from, end_from = get_clinic_date_range_bounds(
        fecha_desde=datetime.date(2027, 6, 7),
    )
    assert start_from == datetime.datetime(2027, 6, 7, 0, 0, 0, tzinfo=AR_TZ)
    assert end_from == datetime.datetime(2100, 1, 2, 0, 0, 0, tzinfo=AR_TZ)

    # 3. Only fecha_hasta provided (inclusive through end of 2027-06-14 -> 2027-06-15 00:00:00)
    start_to, end_to = get_clinic_date_range_bounds(
        fecha_hasta=datetime.date(2027, 6, 14),
    )
    assert start_to == datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=AR_TZ)
    assert end_to == datetime.datetime(2027, 6, 15, 0, 0, 0, tzinfo=AR_TZ)


def test_get_clinic_date_range_bounds_inclusive_range_and_inverted_validation():
    """Task 1.1: Supports multi-day and single-day ranges, and raises ValueError when fecha_hasta < fecha_desde."""
    from app.application.turnos import get_clinic_date_range_bounds

    # Multi-day range: [2027-06-07, 2027-06-14] -> [2027-06-07 00:00:00, 2027-06-15 00:00:00)
    start_rng, end_rng = get_clinic_date_range_bounds(
        fecha_desde=datetime.date(2027, 6, 7),
        fecha_hasta=datetime.date(2027, 6, 14),
        timezone_str="America/Argentina/Buenos_Aires",
    )
    assert start_rng == datetime.datetime(2027, 6, 7, 0, 0, 0, tzinfo=AR_TZ)
    assert end_rng == datetime.datetime(2027, 6, 15, 0, 0, 0, tzinfo=AR_TZ)

    # Single-day range: fecha_desde == fecha_hasta (2027-06-07)
    start_day, end_day = get_clinic_date_range_bounds(
        fecha_desde=datetime.date(2027, 6, 7),
        fecha_hasta=datetime.date(2027, 6, 7),
    )
    assert start_day == datetime.datetime(2027, 6, 7, 0, 0, 0, tzinfo=AR_TZ)
    assert end_day == datetime.datetime(2027, 6, 8, 0, 0, 0, tzinfo=AR_TZ)

    # Inverted range: fecha_hasta < fecha_desde raises ValueError
    with pytest.raises(ValueError, match="fecha_hasta"):
        get_clinic_date_range_bounds(
            fecha_desde=datetime.date(2027, 6, 14),
            fecha_hasta=datetime.date(2027, 6, 7),
        )


def test_find_by_patient_range_eagerly_loads_odontologo_with_selectinload():
    """Task 1.1 (Hard Rule #2): SqlAlchemyTurnoRepository.find_by_patient_range chains selectinload(Turno.odontologo)."""
    import anyio
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.domain.models.base import Base
    from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
    from app.domain.models.turno import Turno
    from app.domain.models.usuario import Usuario
    from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository
    from app.infrastructure.security import hash_password

    # Verify explicitly in source code that selectinload(Turno.odontologo) is configured on find_by_patient_range
    source = inspect.getsource(SqlAlchemyTurnoRepository.find_by_patient_range)
    assert "selectinload(Turno.odontologo)" in source

    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            pac = Usuario(
                nombre="Lucía Gómez (Ficticia)",
                email="lucia.gomez.ficticia@example.com",
                nro_socio="SOC-FICT-601",
                password_hash=hash_password("Pass1234!"),
                rol=RolUsuario.PACIENTE,
                debe_cambiar_password=False,
                perfil_completo=True,
            )
            odo = Usuario(
                nombre="Dra. Sofía Martín (Ficticia)",
                email="sofia.martin.ficticia@example.com",
                nro_socio="ODO-FICT-601",
                password_hash=hash_password("Pass1234!"),
                rol=RolUsuario.ODONTOLOGO,
                debe_cambiar_password=False,
                perfil_completo=True,
            )
            session.add_all([pac, odo])
            await session.commit()
            await session.refresh(pac)
            await session.refresh(odo)

            turno = Turno(
                paciente_id=pac.id,
                odontologo_id=odo.id,
                inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
                fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                motivo="Control general sintético",
                estado=EstadoTurno.CONFIRMADO,
                origen=OrigenTurno.ONLINE,
            )
            session.add(turno)
            await session.commit()

        async with session_factory() as query_session:
            repo = SqlAlchemyTurnoRepository(query_session)
            results = await repo.find_by_patient_range(
                paciente_id=pac.id,
                start=datetime.datetime(2027, 6, 7, 0, 0, tzinfo=AR_TZ),
                end=datetime.datetime(2027, 6, 8, 0, 0, tzinfo=AR_TZ),
            )
            assert len(results) == 1
            # Verify odontologo is already loaded in instance dict without triggering lazy load
            assert "odontologo" in results[0].__dict__
            assert results[0].odontologo.nombre == "Dra. Sofía Martín (Ficticia)"

        await engine.dispose()

    anyio.run(_run)


# =====================================================================
# Task 2.1: Strict Response DTOs & GET /api/mis-turnos for Paciente
# =====================================================================


def test_patient_portal_response_schemas_strict_validation():
    """Task 2.1 (Hard Rule #1 & OWASP BOPLA): OdontologoResumenResponse and MisTurnosPacienteItemResponse enforce extra='forbid'."""
    from pydantic import ValidationError
    from app.api.mis_turnos import MisTurnosPacienteItemResponse, OdontologoResumenResponse
    from app.domain.models.enums import EstadoTurno, OrigenTurno

    odo = OdontologoResumenResponse(
        id=20,
        nombre="Dra. Sofía Martín (Ficticia)",
        nro_socio="ODO-FICT-601",
        email="sofia.martin.ficticia@example.com",
    )
    assert odo.id == 20

    # Reject extra fields such as password_hash, debe_cambiar_password, rol on OdontologoResumenResponse
    for forbidden_extra in (
        {"password_hash": "secret"},
        {"debe_cambiar_password": False},
        {"rol": "odontologo"},
    ):
        with pytest.raises(ValidationError):
            OdontologoResumenResponse(
                id=20,
                nombre="Dra. Sofía Martín (Ficticia)",
                nro_socio="ODO-FICT-601",
                email="sofia.martin.ficticia@example.com",
                **forbidden_extra,
            )

    item = MisTurnosPacienteItemResponse(
        id=1,
        paciente_id=10,
        odontologo_id=20,
        inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
        motivo="Control general sintético",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.ONLINE,
        odontologo=odo,
    )
    assert item.odontologo.nombre == "Dra. Sofía Martín (Ficticia)"

    with pytest.raises(ValidationError):
        MisTurnosPacienteItemResponse(
            id=1,
            paciente_id=10,
            odontologo_id=20,
            inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
            motivo="Control general sintético",
            estado=EstadoTurno.CONFIRMADO,
            origen=OrigenTurno.ONLINE,
            odontologo=odo,
            campo_extra="prohibido",  # type: ignore[call-arg]
        )


@pytest.fixture
def patient_portal_client_and_context():
    import anyio
    from starlette.testclient import TestClient

    from app.domain.models.base import Base
    from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
    from app.domain.models.plantilla import PlantillaDisponibilidad
    from app.domain.models.turno import Turno
    from app.domain.models.usuario import Usuario
    from app.infrastructure.config import Settings
    from app.infrastructure.security import create_access_token, hash_password
    from app.main import create_app

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
                paciente_lucia = Usuario(
                    nombre="Lucía Gómez (Ficticia)",
                    email="lucia.gomez.ficticia@example.com",
                    nro_socio="SOC-FICT-601",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_martin = Usuario(
                    nombre="Martín Pérez (Ficticio)",
                    email="martin.perez.ficticio@example.com",
                    nro_socio="SOC-FICT-602",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_pendiente = Usuario(
                    nombre="Carla Ruiz (Ficticia)",
                    email="carla.ruiz.ficticia@example.com",
                    nro_socio="SOC-FICT-603",
                    password_hash=hash_password("Temp1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=True,
                    perfil_completo=False,
                )
                recepcion = Usuario(
                    nombre="Recepción Central (Ficticia)",
                    email="recepcion.ficticia@example.com",
                    nro_socio=None,
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_sofia = Usuario(
                    nombre="Dra. Sofía Martín (Ficticia)",
                    email="sofia.martin.ficticia@example.com",
                    nro_socio="ODO-FICT-601",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_juan = Usuario(
                    nombre="Dr. Juan Pérez (Ficticio)",
                    email="juan.perez.ficticio@example.com",
                    nro_socio="ODO-FICT-602",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                session.add_all(
                    [
                        paciente_lucia,
                        paciente_martin,
                        paciente_pendiente,
                        recepcion,
                        odontologo_sofia,
                        odontologo_juan,
                    ]
                )
                await session.commit()
                for u in (
                    paciente_lucia,
                    paciente_martin,
                    paciente_pendiente,
                    recepcion,
                    odontologo_sofia,
                    odontologo_juan,
                ):
                    await session.refresh(u)

                # Seed Monday (dia_semana=0) availability template for Dra. Sofía (09:00 to 12:00, 30 min slots)
                plantilla_sofia = PlantillaDisponibilidad(
                    odontologo_id=odontologo_sofia.id,
                    dia_semana=0,  # Monday (2027-06-14 is Monday)
                    hora_inicio=datetime.time(9, 0),
                    hora_fin=datetime.time(12, 0),
                    duracion_slot_minutos=30,
                    prestacion="Odontología General Sintética",
                )
                session.add(plantilla_sofia)

                # Seed appointments for Lucía Gómez across all 6 states, past and future,
                # inserted out of chronological order:
                t_future_confirmado = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_sofia.id,
                    inicio=datetime.datetime(2027, 6, 14, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 14, 9, 30, tzinfo=AR_TZ),
                    motivo="Limpieza futura confirmada sintética",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )
                t_future_solicitado = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_juan.id,
                    inicio=datetime.datetime(2027, 6, 10, 10, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 10, 10, 30, tzinfo=AR_TZ),
                    motivo="Consulta futura solicitada sintética",
                    estado=EstadoTurno.SOLICITADO,
                    origen=OrigenTurno.ONLINE,
                )
                t_range_start = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_sofia.id,
                    inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                    motivo="Turno inicio de rango sintético",
                    estado=EstadoTurno.PRESENTE,
                    origen=OrigenTurno.ONLINE,
                )
                t_past_ausente = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_sofia.id,
                    inicio=datetime.datetime(2026, 5, 4, 11, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2026, 5, 4, 11, 30, tzinfo=AR_TZ),
                    motivo="Turno pasado ausente sintético",
                    estado=EstadoTurno.AUSENTE,
                    origen=OrigenTurno.ONLINE,
                )
                t_past_cancelado = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_juan.id,
                    inicio=datetime.datetime(2027, 6, 6, 23, 30, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 6, 23, 59, tzinfo=AR_TZ),
                    motivo="Turno previo al rango cancelado sintético",
                    estado=EstadoTurno.CANCELADO,
                    origen=OrigenTurno.ONLINE,
                )
                t_after_range_anulado = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_sofia.id,
                    inicio=datetime.datetime(2027, 6, 15, 0, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 15, 0, 30, tzinfo=AR_TZ),
                    motivo="Turno posterior al rango anulado sintético",
                    estado=EstadoTurno.ANULADO,
                    origen=OrigenTurno.MANUAL,
                )

                # Seed appointment for Martín Pérez on the SAME date/time (BOLA cross-patient isolation check)
                t_martin = Turno(
                    paciente_id=paciente_martin.id,
                    odontologo_id=odontologo_juan.id,
                    inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                    motivo="Turno privado de Martín sintético",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )

                session.add_all(
                    [
                        t_future_confirmado,
                        t_future_solicitado,
                        t_range_start,
                        t_past_ausente,
                        t_past_cancelado,
                        t_after_range_anulado,
                        t_martin,
                    ]
                )
                await session.commit()
                await session.refresh(t_future_confirmado)

                return (
                    {
                        "paciente_lucia": paciente_lucia,
                        "paciente_martin": paciente_martin,
                        "paciente_pendiente": paciente_pendiente,
                        "recepcion": recepcion,
                        "odontologo_sofia": odontologo_sofia,
                        "odontologo_juan": odontologo_juan,
                    },
                    {"t_future_confirmado": t_future_confirmado},
                )

        users, seeded_turnos = anyio.run(_seed)
        tokens = {
            key: create_access_token(
                user_id=user.id,
                rol=user.rol,
                debe_cambiar_password=user.debe_cambiar_password,
                settings=settings,
            )
            for key, user in users.items()
        }
        yield client, app, users, tokens, seeded_turnos


def test_get_mis_turnos_patient_unbounded_and_date_range_filtering_with_bola_isolation(
    patient_portal_client_and_context,
):
    """Task 2.1: Patient sees all own past/future appointments sorted by inicio with odontologo summary, never seeing other patients' appointments."""
    client, _app, users, tokens, _seeded = patient_portal_client_and_context
    lucia_id = users["paciente_lucia"].id
    martin_id = users["paciente_martin"].id

    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_martin = {"Authorization": f"Bearer {tokens['paciente_martin']}"}

    # 1. Unbounded GET /api/mis-turnos for Lucía -> returns all 6 of her appointments across all 6 states
    res_all = client.get("/api/mis-turnos", headers=h_lucia)
    assert res_all.status_code == 200
    items = res_all.json()
    assert len(items) == 6

    # Strict BOLA isolation: every returned appointment belongs to Lucía
    assert all(item["paciente_id"] == lucia_id for item in items)

    # Attempting to inject ?paciente_id=<martin_id> in query string still only returns Lucía's appointments
    res_bola_attempt = client.get(
        "/api/mis-turnos",
        params={"paciente_id": martin_id},
        headers=h_lucia,
    )
    assert res_bola_attempt.status_code == 200
    assert all(item["paciente_id"] == lucia_id for item in res_bola_attempt.json())

    # Ascending chronological sort by inicio
    inicios = [datetime.datetime.fromisoformat(item["inicio"]) for item in items]
    assert inicios == sorted(inicios)

    # All 6 lifecycle states present
    estados = {item["estado"] for item in items}
    assert estados == {
        "solicitado",
        "confirmado",
        "presente",
        "ausente",
        "cancelado",
        "anulado",
    }

    # Nested odontologo summary contains only id, nombre, nro_socio, email (no password_hash)
    first_item = items[0]
    assert "odontologo" in first_item
    assert set(first_item["odontologo"].keys()) == {"id", "nombre", "nro_socio", "email"}
    assert "password_hash" not in first_item["odontologo"]

    # 2. Martín queries GET /api/mis-turnos -> sees only his 1 appointment
    res_martin = client.get("/api/mis-turnos", headers=h_martin)
    assert res_martin.status_code == 200
    martin_items = res_martin.json()
    assert len(martin_items) == 1
    assert martin_items[0]["paciente_id"] == martin_id
    assert martin_items[0]["motivo"] == "Turno privado de Martín sintético"

    # 3. Inclusive date range [2027-06-07, 2027-06-14] -> returns exactly the 3 appointments inside [2027-06-07 00:00, 2027-06-15 00:00)
    res_range = client.get(
        "/api/mis-turnos",
        params={"fecha_desde": "2027-06-07", "fecha_hasta": "2027-06-14"},
        headers=h_lucia,
    )
    assert res_range.status_code == 200
    range_items = res_range.json()
    assert len(range_items) == 3
    motivos_rango = [item["motivo"] for item in range_items]
    assert motivos_rango == [
        "Turno inicio de rango sintético",
        "Consulta futura solicitada sintética",
        "Limpieza futura confirmada sintética",
    ]


def test_get_mis_turnos_patient_validation_and_rbac_errors(
    patient_portal_client_and_context,
):
    """Task 2.1: Rejects 401 unauthenticated, 403 recepcion or debe_cambiar_password=True, and 422 inverted range or dentist-only fecha param."""
    client, _app, _users, tokens, _seeded = patient_portal_client_and_context

    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_pendiente = {"Authorization": f"Bearer {tokens['paciente_pendiente']}"}
    h_recepcion = {"Authorization": f"Bearer {tokens['recepcion']}"}

    # 1. 401 Unauthorized without token
    assert client.get("/api/mis-turnos").status_code == 401

    # 2. 403 Forbidden for recepcion role (RN-GL-01)
    assert client.get("/api/mis-turnos", headers=h_recepcion).status_code == 403

    # 3. 403 Forbidden with detail="password_change_required" when paciente has debe_cambiar_password=True
    res_pwd = client.get("/api/mis-turnos", headers=h_pendiente)
    assert res_pwd.status_code == 403
    assert res_pwd.json()["detail"] == "password_change_required"

    # 4. 422 Unprocessable Entity when fecha_hasta < fecha_desde
    res_inv = client.get(
        "/api/mis-turnos",
        params={"fecha_desde": "2027-06-14", "fecha_hasta": "2027-06-07"},
        headers=h_lucia,
    )
    assert res_inv.status_code == 422

    # 5. 422 Unprocessable Entity when paciente passes dentist-only fecha parameter
    res_fecha = client.get(
        "/api/mis-turnos",
        params={"fecha": "2027-06-07"},
        headers=h_lucia,
    )
    assert res_fecha.status_code == 422


def test_patient_portal_e2e_list_and_cancel_appointment_releases_slot(
    patient_portal_client_and_context,
):
    """Task 2.1 (Flujo 5 E2E & US-004): Patient lists future appointment, cancels via PATCH /api/turnos/{id}, sees 'cancelado' in mis-turnos and freed slot in /api/disponibilidad."""
    client, _app, users, tokens, seeded = patient_portal_client_and_context
    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    sofia_id = users["odontologo_sofia"].id
    turno_id = seeded["t_future_confirmado"].id

    # 1. Verify slot 09:00-09:30 on 2027-06-14 is initially occupied in GET /api/disponibilidad
    res_disp_before = client.get(
        "/api/disponibilidad",
        params={"odontologo_id": sofia_id, "fecha": "2027-06-14"},
        headers=h_lucia,
    )
    assert res_disp_before.status_code == 200
    inicios_before = [
        datetime.datetime.fromisoformat(s["inicio"]).time()
        for s in res_disp_before.json()
    ]
    assert datetime.time(9, 0) not in inicios_before

    # 2. Patient cancels the future appointment (>= 24h notice) via PATCH /api/turnos/{id}
    res_cancel = client.patch(
        f"/api/turnos/{turno_id}",
        json={"estado": "cancelado"},
        headers=h_lucia,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["estado"] == "cancelado"

    # 3. Patient queries GET /api/mis-turnos?fecha_desde=2027-06-14&fecha_hasta=2027-06-14 and sees estado="cancelado"
    res_mis_turnos = client.get(
        "/api/mis-turnos",
        params={"fecha_desde": "2027-06-14", "fecha_hasta": "2027-06-14"},
        headers=h_lucia,
    )
    assert res_mis_turnos.status_code == 200
    items = res_mis_turnos.json()
    assert len(items) == 1
    assert items[0]["id"] == turno_id
    assert items[0]["estado"] == "cancelado"

    # 4. Verify slot 09:00-09:30 on 2027-06-14 is now released in GET /api/disponibilidad (CB-03, US-004 CA-2)
    res_disp_after = client.get(
        "/api/disponibilidad",
        params={"odontologo_id": sofia_id, "fecha": "2027-06-14"},
        headers=h_lucia,
    )
    assert res_disp_after.status_code == 200
    inicios_after = [
        datetime.datetime.fromisoformat(s["inicio"]).time()
        for s in res_disp_after.json()
    ]
    assert datetime.time(9, 0) in inicios_after
