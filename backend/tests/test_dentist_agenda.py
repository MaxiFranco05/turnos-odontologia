import datetime
import inspect
from zoneinfo import ZoneInfo

import pytest

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


# =====================================================================
# Task 1.1: Pure Synchronous get_clinic_day_bounds Validator
# =====================================================================


def test_get_clinic_day_bounds_is_pure_synchronous_function():
    """Task 1.1 (Hard Rule #3): get_clinic_day_bounds must be a pure synchronous def function."""
    from app.application.turnos import get_clinic_day_bounds

    assert inspect.isfunction(get_clinic_day_bounds)
    assert not inspect.iscoroutinefunction(get_clinic_day_bounds)


def test_get_clinic_day_bounds_calculates_exact_half_open_day_window():
    """Task 1.1: Computes [00:00:00, +1 day 00:00:00) in America/Argentina/Buenos_Aires across standard and boundary dates."""
    from app.application.turnos import get_clinic_day_bounds

    fecha = datetime.date(2027, 6, 7)
    start, end = get_clinic_day_bounds(fecha)

    assert start == datetime.datetime(2027, 6, 7, 0, 0, 0, tzinfo=AR_TZ)
    assert end == datetime.datetime(2027, 6, 8, 0, 0, 0, tzinfo=AR_TZ)
    assert end - start == datetime.timedelta(days=1)

    # Triangulate: Month/year boundary (2027-12-31 -> 2028-01-01)
    start_ny, end_ny = get_clinic_day_bounds(
        datetime.date(2027, 12, 31),
        timezone_str="America/Argentina/Buenos_Aires",
    )
    assert start_ny == datetime.datetime(2027, 12, 31, 0, 0, 0, tzinfo=AR_TZ)
    assert end_ny == datetime.datetime(2028, 1, 1, 0, 0, 0, tzinfo=AR_TZ)


# =====================================================================
# Task 2.1: Strict Response DTOs & GET /api/mis-turnos Endpoint
# =====================================================================


def test_mis_turnos_response_schemas_strict_validation():
    """Task 2.1 (Hard Rule #1 & OWASP BOPLA): Schemas enforce extra='forbid' and omit sensitive fields."""
    from pydantic import ValidationError
    from app.api.mis_turnos import MisTurnosOdontologoItemResponse, PacienteResumenResponse
    from app.domain.models.enums import EstadoTurno, OrigenTurno

    pac = PacienteResumenResponse(
        id=10,
        nombre="Lucía Gómez (Ficticia)",
        nro_socio="SOC-FICT-501",
        email="lucia.gomez.ficticia@example.com",
    )
    assert pac.id == 10

    # Reject extra fields such as password_hash, debe_cambiar_password, rol on PacienteResumenResponse
    for forbidden_extra in (
        {"password_hash": "secret"},
        {"debe_cambiar_password": False},
        {"rol": "paciente"},
    ):
        with pytest.raises(ValidationError):
            PacienteResumenResponse(
                id=10,
                nombre="Lucía Gómez (Ficticia)",
                nro_socio="SOC-FICT-501",
                email="lucia.gomez.ficticia@example.com",
                **forbidden_extra,
            )

    item = MisTurnosOdontologoItemResponse(
        id=1,
        paciente_id=10,
        odontologo_id=20,
        inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
        motivo="Control general sintético",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.ONLINE,
        paciente=pac,
    )
    assert item.paciente.nombre == "Lucía Gómez (Ficticia)"

    with pytest.raises(ValidationError):
        MisTurnosOdontologoItemResponse(
            id=1,
            paciente_id=10,
            odontologo_id=20,
            inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
            motivo="Control general sintético",
            estado=EstadoTurno.CONFIRMADO,
            origen=OrigenTurno.ONLINE,
            paciente=pac,
            campo_extra="prohibido",  # type: ignore[call-arg]
        )


@pytest.fixture
def dentist_agenda_client_and_context():
    import anyio
    from starlette.testclient import TestClient

    from app.domain.models.base import Base
    from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
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
                    nro_socio="SOC-FICT-501",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_martin = Usuario(
                    nombre="Martín Pérez (Ficticio)",
                    email="martin.perez.ficticio@example.com",
                    nro_socio="SOC-FICT-502",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
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
                    nro_socio="ODO-FICT-501",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_juan = Usuario(
                    nombre="Dr. Juan Pérez (Ficticio)",
                    email="juan.perez.ficticio@example.com",
                    nro_socio="ODO-FICT-502",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_pendiente = Usuario(
                    nombre="Dr. Lucas Díaz (Ficticio)",
                    email="lucas.diaz.ficticio@example.com",
                    nro_socio="ODO-FICT-503",
                    password_hash=hash_password("Temp1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=True,
                    perfil_completo=False,
                )
                session.add_all(
                    [
                        paciente_lucia,
                        paciente_martin,
                        recepcion,
                        odontologo_sofia,
                        odontologo_juan,
                        odontologo_pendiente,
                    ]
                )
                await session.commit()
                for u in (
                    paciente_lucia,
                    paciente_martin,
                    recepcion,
                    odontologo_sofia,
                    odontologo_juan,
                    odontologo_pendiente,
                ):
                    await session.refresh(u)

                # Seed appointments on 2027-06-07 for Dra. Sofía Martín across ALL 6 states,
                # intentionally inserted out of chronological order, including adjacent CB-01 slots
                # (09:00-09:30 and 09:30-10:00) and released states (cancelado/anulado) on the same slot:
                turnos_sofia = [
                    # 11:00-11:30 AUSENTE (inserted first to verify sorting)
                    Turno(
                        paciente_id=paciente_martin.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 11, 0, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 11, 30, tzinfo=AR_TZ),
                        motivo="Control ortodoncia sintético",
                        estado=EstadoTurno.AUSENTE,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # 09:30-10:00 CONFIRMADO (adjacent CB-01 to 09:00-09:30)
                    Turno(
                        paciente_id=paciente_martin.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 10, 0, tzinfo=AR_TZ),
                        motivo="Limpieza dental sintética",
                        estado=EstadoTurno.CONFIRMADO,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # 09:00-09:30 PRESENTE
                    Turno(
                        paciente_id=paciente_lucia.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                        motivo="Consulta inicial sintética",
                        estado=EstadoTurno.PRESENTE,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # 10:00-10:30 CANCELADO (released slot)
                    Turno(
                        paciente_id=paciente_lucia.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 10, 0, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 10, 30, tzinfo=AR_TZ),
                        motivo="Turno cancelado sintético",
                        estado=EstadoTurno.CANCELADO,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # 10:30-11:00 ANULADO (released slot)
                    Turno(
                        paciente_id=paciente_martin.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 10, 30, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 11, 0, tzinfo=AR_TZ),
                        motivo="Turno anulado sintético",
                        estado=EstadoTurno.ANULADO,
                        origen=OrigenTurno.MANUAL,
                    ),
                    # 10:00-10:30 SOLICITADO (re-booked over the cancelled 10:00-10:30 slot, CB-03)
                    Turno(
                        paciente_id=paciente_martin.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 7, 10, 0, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 7, 10, 30, tzinfo=AR_TZ),
                        motivo="Re-reserva 10:00 sintética",
                        estado=EstadoTurno.SOLICITADO,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # Previous day 2027-06-06 23:30-23:59 (must be excluded when querying 2027-06-07)
                    Turno(
                        paciente_id=paciente_lucia.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 6, 23, 30, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 6, 23, 59, tzinfo=AR_TZ),
                        motivo="Turno día previo sintético",
                        estado=EstadoTurno.CONFIRMADO,
                        origen=OrigenTurno.ONLINE,
                    ),
                    # Next day 2027-06-08 00:00-00:30 (must be excluded when querying 2027-06-07)
                    Turno(
                        paciente_id=paciente_lucia.id,
                        odontologo_id=odontologo_sofia.id,
                        inicio=datetime.datetime(2027, 6, 8, 0, 0, tzinfo=AR_TZ),
                        fin=datetime.datetime(2027, 6, 8, 0, 30, tzinfo=AR_TZ),
                        motivo="Turno día siguiente sintético",
                        estado=EstadoTurno.CONFIRMADO,
                        origen=OrigenTurno.ONLINE,
                    ),
                ]

                # Seed appointment on the SAME date 2027-06-07 for Dr. Juan Pérez (BOLA isolation check)
                turno_juan = Turno(
                    paciente_id=paciente_lucia.id,
                    odontologo_id=odontologo_juan.id,
                    inicio=datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ),
                    fin=datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ),
                    motivo="Endodoncia con Dr. Juan sintética",
                    estado=EstadoTurno.CONFIRMADO,
                    origen=OrigenTurno.ONLINE,
                )

                session.add_all([*turnos_sofia, turno_juan])
                await session.commit()

                return {
                    "paciente_lucia": paciente_lucia,
                    "paciente_martin": paciente_martin,
                    "recepcion": recepcion,
                    "odontologo_sofia": odontologo_sofia,
                    "odontologo_juan": odontologo_juan,
                    "odontologo_pendiente": odontologo_pendiente,
                }

        users = anyio.run(_seed)
        tokens = {
            key: create_access_token(
                user_id=user.id,
                rol=user.rol,
                debe_cambiar_password=user.debe_cambiar_password,
                settings=settings,
            )
            for key, user in users.items()
        }
        yield client, app, users, tokens


def test_get_mis_turnos_dentist_happy_path_bola_isolation_and_date_boundaries(
    dentist_agenda_client_and_context,
):
    """Task 2.1: Dentist sees only own appointments on fecha across all 6 states sorted by inicio with patient summary."""
    client, _app, users, tokens = dentist_agenda_client_and_context
    sofia_id = users["odontologo_sofia"].id
    juan_id = users["odontologo_juan"].id

    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}
    h_juan = {"Authorization": f"Bearer {tokens['odontologo_juan']}"}

    # 1. Dra. Sofía queries 2027-06-07 -> returns exactly her 6 appointments on that date, sorted by inicio
    res_sofia = client.get(
        "/api/mis-turnos",
        params={"fecha": "2027-06-07"},
        headers=h_sofia,
    )
    assert res_sofia.status_code == 200
    items = res_sofia.json()
    assert len(items) == 6

    # Verify strict BOLA isolation: all items belong to Dra. Sofía, none to Dr. Juan
    assert all(item["odontologo_id"] == sofia_id for item in items)

    # Verify ascending chronological order by inicio
    inicios = [datetime.datetime.fromisoformat(item["inicio"]) for item in items]
    assert inicios == sorted(inicios)

    # Verify all 6 lifecycle states are present
    estados = {item["estado"] for item in items}
    assert estados == {
        "solicitado",
        "confirmado",
        "presente",
        "ausente",
        "cancelado",
        "anulado",
    }

    # Verify nested paciente summary contains only id, nombre, nro_socio, email (no password_hash)
    first_item = items[0]
    assert "paciente" in first_item
    assert set(first_item["paciente"].keys()) == {"id", "nombre", "nro_socio", "email"}
    assert first_item["paciente"]["nombre"] == "Lucía Gómez (Ficticia)"
    assert first_item["paciente"]["nro_socio"] == "SOC-FICT-501"

    # 2. Dr. Juan queries the same date 2027-06-07 -> sees only his 1 appointment
    res_juan = client.get(
        "/api/mis-turnos",
        params={"fecha": "2027-06-07"},
        headers=h_juan,
    )
    assert res_juan.status_code == 200
    juan_items = res_juan.json()
    assert len(juan_items) == 1
    assert juan_items[0]["odontologo_id"] == juan_id
    assert juan_items[0]["motivo"] == "Endodoncia con Dr. Juan sintética"

    # 3. Empty day returns []
    res_empty = client.get(
        "/api/mis-turnos",
        params={"fecha": "2027-06-09"},
        headers=h_sofia,
    )
    assert res_empty.status_code == 200
    assert res_empty.json() == []


def test_get_mis_turnos_rbac_password_and_query_validation_errors(
    dentist_agenda_client_and_context,
):
    """Task 2.1: Rejects 401 unauthenticated, 403 paciente/recepcion/debe_cambiar_password, and 422 missing/invalid fecha."""
    client, _app, _users, tokens = dentist_agenda_client_and_context

    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_recepcion = {"Authorization": f"Bearer {tokens['recepcion']}"}
    h_pendiente = {"Authorization": f"Bearer {tokens['odontologo_pendiente']}"}
    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}

    # 1. 401 Unauthorized without token
    assert client.get("/api/mis-turnos", params={"fecha": "2027-06-07"}).status_code == 401

    # 2. 403 Forbidden for recepcion role (RN-GL-01) and 422 for paciente passing dentist-only fecha parameter
    assert (
        client.get(
            "/api/mis-turnos",
            params={"fecha": "2027-06-07"},
            headers=h_lucia,
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/mis-turnos",
            params={"fecha": "2027-06-07"},
            headers=h_recepcion,
        ).status_code
        == 403
    )

    # 3. 403 Forbidden when odontologo has debe_cambiar_password=True (US-010)
    res_pwd = client.get(
        "/api/mis-turnos",
        params={"fecha": "2027-06-07"},
        headers=h_pendiente,
    )
    assert res_pwd.status_code == 403
    assert res_pwd.json()["detail"] == "password_change_required"

    # 4. 422 Unprocessable Entity on missing or malformed fecha or patient-only params for odontologo
    assert client.get("/api/mis-turnos", headers=h_sofia).status_code == 422
    assert (
        client.get(
            "/api/mis-turnos",
            params={"fecha": "2027-06-07", "fecha_desde": "2027-06-01"},
            headers=h_sofia,
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/mis-turnos",
            params={"fecha": "fecha-invalida"},
            headers=h_sofia,
        ).status_code
        == 422
    )


# =====================================================================
# C-22 Task 1.1: Pure Synchronous Month Helpers for Dentist Calendar
# =====================================================================


def test_month_calendar_helpers_are_pure_synchronous_functions():
    """C-22 Task 1.1 (Hard Rule #3): Month helpers must be pure synchronous def functions."""
    from app.application.turnos import (
        get_clinic_month_bounds,
        summarize_dentist_month_appointments,
    )

    assert inspect.isfunction(get_clinic_month_bounds)
    assert not inspect.iscoroutinefunction(get_clinic_month_bounds)
    assert inspect.isfunction(summarize_dentist_month_appointments)
    assert not inspect.iscoroutinefunction(summarize_dentist_month_appointments)


def test_get_clinic_month_bounds_handles_standard_and_december_rollover():
    """C-22 Task 1.1: Computes [first_day 00:00, next_month_first_day 00:00) in clinic TZ."""
    from app.application.turnos import get_clinic_month_bounds

    start_nov, end_nov = get_clinic_month_bounds(2026, 11)
    assert start_nov == datetime.datetime(2026, 11, 1, 0, 0, 0, tzinfo=AR_TZ)
    assert end_nov == datetime.datetime(2026, 12, 1, 0, 0, 0, tzinfo=AR_TZ)

    # Triangulate December -> January rollover and invalid month
    start_dec, end_dec = get_clinic_month_bounds(2026, 12, timezone_str="America/Argentina/Buenos_Aires")
    assert start_dec == datetime.datetime(2026, 12, 1, 0, 0, 0, tzinfo=AR_TZ)
    assert end_dec == datetime.datetime(2027, 1, 1, 0, 0, 0, tzinfo=AR_TZ)

    with pytest.raises(ValueError):
        get_clinic_month_bounds(2026, 13)
    with pytest.raises(ValueError):
        get_clinic_month_bounds(2026, 0)


def test_summarize_dentist_month_appointments_groups_by_clinic_date_and_excludes_cancelled():
    """C-22 Task 1.1 (CB-03, CB-05, RN-TU-04): Groups active appointments in clinic TZ and excludes cancelado/anulado."""
    from types import SimpleNamespace
    from app.application.turnos import summarize_dentist_month_appointments
    from app.domain.models.enums import EstadoTurno

    utc = datetime.timezone.utc
    turnos = [
        # 2026-11-30 22:00 AR == 2026-12-01 01:00 UTC -> must count in 2026-11-30 (CB-05)
        SimpleNamespace(
            inicio=datetime.datetime(2026, 12, 1, 1, 0, tzinfo=utc),
            estado=EstadoTurno.CONFIRMADO,
        ),
        # Same day 2026-11-30 with solicitado
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 30, 14, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.SOLICITADO,
        ),
        # 2026-11-13: 1 presente + 1 ausente + 1 cancelado + 1 anulado (CB-03)
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 13, 9, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.PRESENTE,
        ),
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 13, 10, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.AUSENTE,
        ),
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 13, 11, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.CANCELADO,
        ),
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 13, 12, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.ANULADO,
        ),
        # 2026-11-14: ONLY cancelado -> must NOT appear in summary
        SimpleNamespace(
            inicio=datetime.datetime(2026, 11, 14, 15, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.CANCELADO,
        ),
        # Out-of-month appointment (2026-12-01 09:00 AR) -> must NOT count in November
        SimpleNamespace(
            inicio=datetime.datetime(2026, 12, 1, 9, 0, tzinfo=AR_TZ),
            estado=EstadoTurno.CONFIRMADO,
        ),
    ]

    summary = summarize_dentist_month_appointments(turnos, anio=2026, mes=11)

    assert summary == [
        {
            "fecha": datetime.date(2026, 11, 13),
            "confirmados": 0,
            "solicitados": 0,
            "atendidos": 2,
            "total_activos": 2,
        },
        {
            "fecha": datetime.date(2026, 11, 30),
            "confirmados": 1,
            "solicitados": 1,
            "atendidos": 0,
            "total_activos": 2,
        },
    ]


# =====================================================================
# C-22 Task 1.2: GET /api/mis-turnos/calendario Endpoint & Strict DTOs
# =====================================================================


def test_calendario_response_schemas_enforce_extra_forbid():
    """C-22 Task 1.2 (Hard Rule #1): Calendario schemas must reject undeclared fields."""
    from pydantic import ValidationError
    from app.api.mis_turnos import CalendarioDiaResumenResponse, CalendarioMesResponse

    dia = CalendarioDiaResumenResponse(
        fecha=datetime.date(2027, 6, 7),
        confirmados=2,
        solicitados=1,
        atendidos=0,
        total_activos=3,
    )
    mes = CalendarioMesResponse(anio=2027, mes=6, dias=[dia])
    assert mes.dias[0].total_activos == 3

    with pytest.raises(ValidationError):
        CalendarioDiaResumenResponse(
            fecha=datetime.date(2027, 6, 7),
            confirmados=2,
            solicitados=1,
            atendidos=0,
            total_activos=3,
            extra_field="nope",
        )

    with pytest.raises(ValidationError):
        CalendarioMesResponse(anio=2027, mes=6, dias=[dia], extra_field="nope")


def test_get_mis_turnos_calendario_returns_sorted_summary_and_isolates_dentist(
    dentist_agenda_client_and_context,
):
    """C-22 Task 1.2: Returns monthly active counts for authenticated dentist only, excluding cancelado/anulado."""
    client, _app, users, tokens = dentist_agenda_client_and_context
    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}
    h_juan = {"Authorization": f"Bearer {tokens['odontologo_juan']}"}

    # In fixture, June 2027 has for Sofia:
    # - 2027-06-07: 1 confirmado, 1 solicitado, 1 presente, 1 cancelado, 1 anulado -> total_activos=3
    # - 2027-06-08: 1 confirmado
    # And Juan has 1 confirmado on 2027-06-07 (must NOT appear for Sofia)
    res_sofia = client.get(
        "/api/mis-turnos/calendario",
        params={"anio": 2027, "mes": 6},
        headers=h_sofia,
    )
    assert res_sofia.status_code == 200
    assert res_sofia.json() == {
        "anio": 2027,
        "mes": 6,
        "dias": [
            {
                "fecha": "2027-06-06",
                "confirmados": 1,
                "solicitados": 0,
                "atendidos": 0,
                "total_activos": 1,
            },
            {
                "fecha": "2027-06-07",
                "confirmados": 1,
                "solicitados": 1,
                "atendidos": 2,
                "total_activos": 4,
            },
            {
                "fecha": "2027-06-08",
                "confirmados": 1,
                "solicitados": 0,
                "atendidos": 0,
                "total_activos": 1,
            },
        ],
    }

    res_juan = client.get(
        "/api/mis-turnos/calendario",
        params={"anio": 2027, "mes": 6},
        headers=h_juan,
    )
    assert res_juan.status_code == 200
    assert res_juan.json() == {
        "anio": 2027,
        "mes": 6,
        "dias": [
            {
                "fecha": "2027-06-07",
                "confirmados": 1,
                "solicitados": 0,
                "atendidos": 0,
                "total_activos": 1,
            }
        ],
    }

    # Defaults without anio/mes resolve current clinic year/month cleanly
    res_default = client.get("/api/mis-turnos/calendario", headers=h_sofia)
    assert res_default.status_code == 200
    today_clinic = datetime.datetime.now(AR_TZ).date()
    assert res_default.json()["anio"] == today_clinic.year
    assert res_default.json()["mes"] == today_clinic.month
    assert res_default.json()["dias"] == []


def test_get_mis_turnos_calendario_rbac_and_query_validation(
    dentist_agenda_client_and_context,
):
    """C-22 Task 1.2 (CB-06, RN-GL-01): Enforces 401, 403 for non-dentist / pending password, and 422 on invalid month."""
    client, _app, _users, tokens = dentist_agenda_client_and_context
    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_recepcion = {"Authorization": f"Bearer {tokens['recepcion']}"}
    h_pendiente = {"Authorization": f"Bearer {tokens['odontologo_pendiente']}"}
    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}

    assert client.get("/api/mis-turnos/calendario").status_code == 401
    assert client.get("/api/mis-turnos/calendario", headers=h_lucia).status_code == 403
    assert client.get("/api/mis-turnos/calendario", headers=h_recepcion).status_code == 403

    res_pwd = client.get("/api/mis-turnos/calendario", headers=h_pendiente)
    assert res_pwd.status_code == 403
    assert res_pwd.json()["detail"] == "password_change_required"

    assert (
        client.get(
            "/api/mis-turnos/calendario",
            params={"anio": 2027, "mes": 0},
            headers=h_sofia,
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/mis-turnos/calendario",
            params={"anio": 2027, "mes": 13},
            headers=h_sofia,
        ).status_code
        == 422
    )



