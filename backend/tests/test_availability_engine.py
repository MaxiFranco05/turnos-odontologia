import datetime
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.plantilla import SqlAlchemyPlantillaRepository


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def dentist_user(async_session: AsyncSession):
    dentist = Usuario(
        nombre="Dra. Sofía Martín (Ficticia)",
        email="sofia.martin.ficticia@example.com",
        nro_socio="ODO-TEST-001",
        password_hash="pw_hash_test",
        rol=RolUsuario.ODONTOLOGO,
    )
    async_session.add(dentist)
    await async_session.commit()
    await async_session.refresh(dentist)
    return dentist


@pytest.fixture
async def second_dentist_user(async_session: AsyncSession):
    dentist2 = Usuario(
        nombre="Dr. Juan Pérez (Ficticio)",
        email="juan.perez.ficticio@example.com",
        nro_socio="ODO-TEST-002",
        password_hash="pw_hash_test_2",
        rol=RolUsuario.ODONTOLOGO,
    )
    async_session.add(dentist2)
    await async_session.commit()
    await async_session.refresh(dentist2)
    return dentist2


@pytest.mark.asyncio
async def test_find_overlapping_templates_cases(
    async_session: AsyncSession,
    dentist_user: Usuario,
    second_dentist_user: Usuario,
):
    repo = SqlAlchemyPlantillaRepository(session=async_session)

    # Base template: Monday (dia_semana=0) 09:00 to 12:00
    base_template = PlantillaDisponibilidad(
        odontologo_id=dentist_user.id,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(12, 0),
        duracion_slot_minutos=30,
        prestacion="Consulta General",
    )
    async_session.add(base_template)
    await async_session.commit()
    await async_session.refresh(base_template)

    # 1. Enclosed interval: 10:00 to 11:00 -> overlaps
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(10, 0), datetime.time(11, 0)
    )
    assert len(overlaps) == 1
    assert overlaps[0].id == base_template.id

    # 2. Enclosing interval: 08:00 to 13:00 -> overlaps
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(8, 0), datetime.time(13, 0)
    )
    assert len(overlaps) == 1

    # 3. Partial overlap left: 08:00 to 10:00 -> overlaps
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(8, 0), datetime.time(10, 0)
    )
    assert len(overlaps) == 1

    # 4. Partial overlap right: 11:00 to 13:00 -> overlaps
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(11, 0), datetime.time(13, 0)
    )
    assert len(overlaps) == 1

    # 5. CB-01 Adjacency after: 12:00 to 14:00 (fin == inicio) -> NO overlap
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(12, 0), datetime.time(14, 0)
    )
    assert len(overlaps) == 0

    # 6. CB-01 Adjacency before: 07:00 to 09:00 (fin == inicio) -> NO overlap
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 0, datetime.time(7, 0), datetime.time(9, 0)
    )
    assert len(overlaps) == 0

    # 7. Different day: Tuesday (dia_semana=1) 09:00 to 12:00 -> NO overlap
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id, 1, datetime.time(9, 0), datetime.time(12, 0)
    )
    assert len(overlaps) == 0

    # 8. Different dentist: same day/time for second_dentist -> NO overlap
    overlaps = await repo.find_overlapping_templates(
        second_dentist_user.id, 0, datetime.time(9, 0), datetime.time(12, 0)
    )
    assert len(overlaps) == 0

    # 9. exclude_id excludes the base template during self-update
    overlaps = await repo.find_overlapping_templates(
        dentist_user.id,
        0,
        datetime.time(9, 0),
        datetime.time(12, 0),
        exclude_id=base_template.id,
    )
    assert len(overlaps) == 0


def test_calculate_free_slots_red():
    from app.application.availability import calculate_free_slots

    template = PlantillaDisponibilidad(
        odontologo_id=1,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(10, 30),
        duracion_slot_minutos=30,
        prestacion="Consulta General",
    )
    fecha = datetime.date(2026, 11, 9)  # Future Monday
    slots = calculate_free_slots(
        fecha=fecha,
        templates=[template],
        turnos=[],
        now_override=datetime.datetime(2026, 11, 2, 8, 0, tzinfo=datetime.timezone.utc),
    )
    assert len(slots) == 3


def test_calculate_free_slots_scenarios_and_edge_cases():
    from zoneinfo import ZoneInfo
    from app.application.availability import calculate_free_slots
    from app.domain.models.enums import EstadoTurno, OrigenTurno
    from app.domain.models.turno import Turno

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    future_monday = datetime.date(2026, 11, 16)
    simulated_now = datetime.datetime(2026, 11, 2, 8, 0, tzinfo=tz)

    # 1. Expected behavior: active appointment subtracts slot
    template = PlantillaDisponibilidad(
        odontologo_id=10,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(10, 30),
        duracion_slot_minutos=30,
        prestacion="Consulta General",
    )
    active_appt = Turno(
        paciente_id=1,
        odontologo_id=10,
        inicio=datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=tz),
        fin=datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=tz),
        motivo="Revisión",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.ONLINE,
    )
    slots = calculate_free_slots(
        fecha=future_monday,
        templates=[template],
        turnos=[active_appt],
        now_override=simulated_now,
    )
    assert len(slots) == 2
    assert slots[0].inicio.time() == datetime.time(9, 0)
    assert slots[0].fin.time() == datetime.time(9, 30)
    assert slots[1].inicio.time() == datetime.time(10, 0)
    assert slots[1].fin.time() == datetime.time(10, 30)

    # 2. CB-03: Cancelled or Annulled appointments release slot
    cancelled_appt = Turno(
        paciente_id=1,
        odontologo_id=10,
        inicio=datetime.datetime.combine(future_monday, datetime.time(9, 0), tzinfo=tz),
        fin=datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=tz),
        motivo="Cancelado por paciente",
        estado=EstadoTurno.CANCELADO,
        origen=OrigenTurno.ONLINE,
    )
    annulled_appt = Turno(
        paciente_id=2,
        odontologo_id=10,
        inicio=datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=tz),
        fin=datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=tz),
        motivo="Anulado por recepcion",
        estado=EstadoTurno.ANULADO,
        origen=OrigenTurno.ONLINE,
    )
    slots_libres = calculate_free_slots(
        fecha=future_monday,
        templates=[template],
        turnos=[cancelled_appt, annulled_appt],
        now_override=simulated_now,
    )
    assert len(slots_libres) == 3

    # 3. CB-02: Remainder incomplete slot discarded
    tpl_remainder = PlantillaDisponibilidad(
        odontologo_id=10,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(10, 0),  # 60 min window
        duracion_slot_minutos=40,       # 40 min slot -> only 09:00-09:40 valid
        prestacion="Limpieza",
    )
    slots_remainder = calculate_free_slots(
        fecha=future_monday,
        templates=[tpl_remainder],
        turnos=[],
        now_override=simulated_now,
    )
    assert len(slots_remainder) == 1
    assert slots_remainder[0].inicio.time() == datetime.time(9, 0)
    assert slots_remainder[0].fin.time() == datetime.time(9, 40)

    # 4. CB-04: Off-grid appointment blocks all intersected slots
    tpl_two_hours = PlantillaDisponibilidad(
        odontologo_id=10,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(11, 0),  # 4 slots: 09:00-09:30, 09:30-10:00, 10:00-10:30, 10:30-11:00
        duracion_slot_minutos=30,
        prestacion="Consulta",
    )
    straddling_appt = Turno(
        paciente_id=3,
        odontologo_id=10,
        inicio=datetime.datetime.combine(future_monday, datetime.time(9, 15), tzinfo=tz),
        fin=datetime.datetime.combine(future_monday, datetime.time(10, 15), tzinfo=tz),
        motivo="Cirugía",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.ONLINE,
    )
    slots_straddled = calculate_free_slots(
        fecha=future_monday,
        templates=[tpl_two_hours],
        turnos=[straddling_appt],
        now_override=simulated_now,
    )
    assert len(slots_straddled) == 1
    assert slots_straddled[0].inicio.time() == datetime.time(10, 30)
    assert slots_straddled[0].fin.time() == datetime.time(11, 0)

    # 5. CB-05: Today's elapsed morning slots filtered out
    today_monday = datetime.date(2026, 11, 2)
    today_now = datetime.datetime(2026, 11, 2, 10, 15, tzinfo=tz)
    slots_today = calculate_free_slots(
        fecha=today_monday,
        templates=[tpl_two_hours],
        turnos=[],
        now_override=today_now,
    )
    assert len(slots_today) == 1
    assert slots_today[0].inicio.time() == datetime.time(10, 30)

    # 6. Past date raises ValueError (RN-GL-02)
    yesterday = datetime.date(2026, 11, 1)
    with pytest.raises(ValueError, match="fechas pasadas"):
        calculate_free_slots(
            fecha=yesterday,
            templates=[tpl_two_hours],
            turnos=[],
            now_override=today_now,
        )


def test_plantillas_schemas_validation_red():
    from pydantic import ValidationError
    from app.api.plantillas import PlantillaCreate, PlantillaUpdate

    # Valid template creation
    valid = PlantillaCreate(
        odontologo_id=1,
        dia_semana=0,
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(13, 0),
        duracion_slot_minutos=30,
        prestacion="Consulta",
    )
    assert valid.dia_semana == 0

    # Inverted time range: hora_fin <= hora_inicio
    with pytest.raises(ValidationError):
        PlantillaCreate(
            odontologo_id=1,
            dia_semana=0,
            hora_inicio=datetime.time(13, 0),
            hora_fin=datetime.time(9, 0),
            duracion_slot_minutos=30,
            prestacion="Consulta",
        )

    # Extra field forbidden (Hard Rule #1)
    with pytest.raises(ValidationError):
        PlantillaCreate(
            odontologo_id=1,
            dia_semana=0,
            hora_inicio=datetime.time(9, 0),
            hora_fin=datetime.time(13, 0),
            duracion_slot_minutos=30,
            prestacion="Consulta",
            box=1,  # type: ignore
        )

    # Invalid dia_semana (>6)
    with pytest.raises(ValidationError):
        PlantillaCreate(
            odontologo_id=1,
            dia_semana=7,
            hora_inicio=datetime.time(9, 0),
            hora_fin=datetime.time(13, 0),
            duracion_slot_minutos=30,
            prestacion="Consulta",
        )

    # Non-positive duracion_slot_minutos (<=0)
    with pytest.raises(ValidationError):
        PlantillaCreate(
            odontologo_id=1,
            dia_semana=0,
            hora_inicio=datetime.time(9, 0),
            hora_fin=datetime.time(13, 0),
            duracion_slot_minutos=0,
            prestacion="Consulta",
        )


@pytest.fixture
def app_with_synthetic_users():
    import anyio
    from starlette.testclient import TestClient
    from app.domain.models.base import Base
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
                paciente = Usuario(
                    nombre="Paciente Sintético (Ficticio)",
                    email="paciente.ficticio@example.com",
                    nro_socio="SOC-TEST-100",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                recepcion = Usuario(
                    nombre="Recepción Sintética (Ficticia)",
                    email="recepcion.ficticia@example.com",
                    nro_socio=None,
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.RECEPCION,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo = Usuario(
                    nombre="Dra. Sofía Martín (Ficticia)",
                    email="sofia.martin.ficticia@example.com",
                    nro_socio="ODO-TEST-200",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_2 = Usuario(
                    nombre="Dr. Juan Pérez (Ficticio)",
                    email="juan.perez.ficticio@example.com",
                    nro_socio="ODO-TEST-201",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                session.add_all([paciente, recepcion, odontologo, odontologo_2])
                await session.commit()
                await session.refresh(paciente)
                await session.refresh(recepcion)
                await session.refresh(odontologo)
                await session.refresh(odontologo_2)
                return {
                    "paciente": paciente,
                    "recepcion": recepcion,
                    "odontologo": odontologo,
                    "odontologo_2": odontologo_2,
                }

        users = anyio.run(_seed)

        tokens = {
            "paciente": create_access_token(
                user_id=users["paciente"].id,
                rol=RolUsuario.PACIENTE,
                debe_cambiar_password=False,
                settings=settings,
            ),
            "recepcion": create_access_token(
                user_id=users["recepcion"].id,
                rol=RolUsuario.RECEPCION,
                debe_cambiar_password=False,
                settings=settings,
            ),
            "odontologo": create_access_token(
                user_id=users["odontologo"].id,
                rol=RolUsuario.ODONTOLOGO,
                debe_cambiar_password=False,
                settings=settings,
            ),
            "odontologo_2": create_access_token(
                user_id=users["odontologo_2"].id,
                rol=RolUsuario.ODONTOLOGO,
                debe_cambiar_password=False,
                settings=settings,
            ),
        }

        yield {
            "client": client,
            "users": users,
            "tokens": tokens,
            "settings": settings,
        }


def test_plantillas_crud_endpoints_red(app_with_synthetic_users):
    client = app_with_synthetic_users["client"]
    recepcion_token = app_with_synthetic_users["tokens"]["recepcion"]
    dentist_id = app_with_synthetic_users["users"]["odontologo"].id

    headers = {"Authorization": f"Bearer {recepcion_token}"}
    payload = {
        "odontologo_id": dentist_id,
        "dia_semana": 0,
        "hora_inicio": "09:00:00",
        "hora_fin": "13:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Consulta general",
    }
    response = client.post("/api/plantillas", json=payload, headers=headers)
    assert response.status_code == 201


def test_plantillas_api_full_scenarios_and_edge_cases(app_with_synthetic_users):
    client = app_with_synthetic_users["client"]
    tokens = app_with_synthetic_users["tokens"]
    users = app_with_synthetic_users["users"]

    rec_headers = {"Authorization": f"Bearer {tokens['recepcion']}"}
    pac_headers = {"Authorization": f"Bearer {tokens['paciente']}"}
    odo_headers = {"Authorization": f"Bearer {tokens['odontologo']}"}

    dentist_id = users["odontologo"].id
    patient_id = users["paciente"].id

    # 1. Expected behavior: Create valid template (201 Created)
    payload_1 = {
        "odontologo_id": dentist_id,
        "dia_semana": 0,
        "hora_inicio": "09:00:00",
        "hora_fin": "11:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Consulta General",
    }
    res_create = client.post("/api/plantillas", json=payload_1, headers=rec_headers)
    assert res_create.status_code == 201
    tpl_1_id = res_create.json()["id"]

    # 2. CB-01: Contiguous adjacent template on same day is accepted (201 Created)
    payload_contiguous = {
        "odontologo_id": dentist_id,
        "dia_semana": 0,
        "hora_inicio": "11:00:00",
        "hora_fin": "13:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Ortodoncia",
    }
    res_contig = client.post("/api/plantillas", json=payload_contiguous, headers=rec_headers)
    assert res_contig.status_code == 201
    tpl_2_id = res_contig.json()["id"]

    # 3. Business error: Overlapping template on same day/dentist (409 Conflict)
    payload_overlap = {
        "odontologo_id": dentist_id,
        "dia_semana": 0,
        "hora_inicio": "10:30:00",
        "hora_fin": "12:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Endodoncia",
    }
    res_overlap = client.post("/api/plantillas", json=payload_overlap, headers=rec_headers)
    assert res_overlap.status_code == 409

    # 4. Business error: RBAC 403 Forbidden for paciente and odontologo
    res_pac = client.post("/api/plantillas", json=payload_1, headers=pac_headers)
    assert res_pac.status_code == 403
    res_odo = client.post("/api/plantillas", json=payload_1, headers=odo_headers)
    assert res_odo.status_code == 403

    # 5. Business error: Non-existent dentist (404 Not Found)
    payload_missing_dentist = {
        "odontologo_id": 999999,
        "dia_semana": 1,
        "hora_inicio": "09:00:00",
        "hora_fin": "12:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Consulta",
    }
    res_missing_dentist = client.post("/api/plantillas", json=payload_missing_dentist, headers=rec_headers)
    assert res_missing_dentist.status_code == 404

    # 6. Business error: Non-dentist user (422 Unprocessable Entity)
    payload_patient_as_dentist = {
        "odontologo_id": patient_id,
        "dia_semana": 1,
        "hora_inicio": "09:00:00",
        "hora_fin": "12:00:00",
        "duracion_slot_minutos": 30,
        "prestacion": "Consulta",
    }
    res_non_dentist = client.post("/api/plantillas", json=payload_patient_as_dentist, headers=rec_headers)
    assert res_non_dentist.status_code == 422

    # 7. List templates filtered by dentist (200 OK)
    res_list = client.get(f"/api/plantillas?odontologo_id={dentist_id}", headers=rec_headers)
    assert res_list.status_code == 200
    listed = res_list.json()
    assert len(listed) >= 2

    # 8. Edge Case: Empty PATCH payload {} is an idempotent no-op (200 OK)
    res_patch_noop = client.patch(f"/api/plantillas/{tpl_1_id}", json={}, headers=rec_headers)
    assert res_patch_noop.status_code == 200
    assert res_patch_noop.json()["hora_fin"] == "11:00:00"

    # 9. Edge Case: PATCH setting hora_fin <= stored hora_inicio (422 Unprocessable Entity)
    res_patch_invert = client.patch(
        f"/api/plantillas/{tpl_1_id}",
        json={"hora_fin": "08:30:00"},
        headers=rec_headers,
    )
    assert res_patch_invert.status_code == 422

    # 10. Business error: PATCH introducing overlap into tpl_2 (409 Conflict)
    res_patch_overlap = client.patch(
        f"/api/plantillas/{tpl_1_id}",
        json={"hora_fin": "12:00:00"},  # Collides with tpl_2 which starts at 11:00
        headers=rec_headers,
    )
    assert res_patch_overlap.status_code == 409

    # 11. Expected behavior: Valid partial PATCH (200 OK)
    res_patch_valid = client.patch(
        f"/api/plantillas/{tpl_1_id}",
        json={"duracion_slot_minutos": 20, "prestacion": "Control"},
        headers=rec_headers,
    )
    assert res_patch_valid.status_code == 200
    assert res_patch_valid.json()["duracion_slot_minutos"] == 20
    assert res_patch_valid.json()["prestacion"] == "Control"

    # 12. Non-existent template PATCH (404 Not Found)
    res_patch_404 = client.patch("/api/plantillas/999999", json={"duracion_slot_minutos": 15}, headers=rec_headers)
    assert res_patch_404.status_code == 404

    # 13. Non-existent template DELETE (404 Not Found)
    res_delete_404 = client.delete("/api/plantillas/999999", headers=rec_headers)
    assert res_delete_404.status_code == 404

    # 14. Expected behavior: DELETE template (204 No Content)
    res_delete = client.delete(f"/api/plantillas/{tpl_2_id}", headers=rec_headers)
    assert res_delete.status_code == 204


def test_disponibilidad_endpoint_red(app_with_synthetic_users):
    client = app_with_synthetic_users["client"]
    paciente_token = app_with_synthetic_users["tokens"]["paciente"]
    dentist_id = app_with_synthetic_users["users"]["odontologo"].id

    headers = {"Authorization": f"Bearer {paciente_token}"}
    future_date = "2026-11-16"
    response = client.get(
        f"/api/disponibilidad?odontologo_id={dentist_id}&fecha={future_date}",
        headers=headers,
    )
    assert response.status_code == 200


def test_disponibilidad_api_full_scenarios_and_edge_cases(app_with_synthetic_users):
    import anyio
    from zoneinfo import ZoneInfo
    from app.domain.models.enums import EstadoTurno, OrigenTurno
    from app.domain.models.plantilla import PlantillaDisponibilidad
    from app.domain.models.turno import Turno

    client = app_with_synthetic_users["client"]
    tokens = app_with_synthetic_users["tokens"]
    users = app_with_synthetic_users["users"]
    app = client.app
    tz = ZoneInfo("America/Argentina/Buenos_Aires")

    pac_headers = {"Authorization": f"Bearer {tokens['paciente']}"}
    dentist_id = users["odontologo"].id
    patient_id = users["paciente"].id

    future_monday = datetime.date(2026, 11, 23)

    # Seed templates and appointments in DB
    async def _setup_data():
        async with app.state.session_factory() as session:
            # Template 1: Monday 09:00 - 11:00 (30 min slots)
            tpl = PlantillaDisponibilidad(
                odontologo_id=dentist_id,
                dia_semana=0,
                hora_inicio=datetime.time(9, 0),
                hora_fin=datetime.time(11, 0),
                duracion_slot_minutos=30,
                prestacion="Consulta General",
            )
            # Template 2 for another dentist with 40-minute slots (CB-02 test)
            tpl_cb2 = PlantillaDisponibilidad(
                odontologo_id=users["odontologo_2"].id,
                dia_semana=0,
                hora_inicio=datetime.time(9, 0),
                hora_fin=datetime.time(10, 0),
                duracion_slot_minutos=40,
                prestacion="Limpieza Dental",
            )
            # Turno 1: Active confirmed appointment on 09:30 - 10:00
            t_active = Turno(
                paciente_id=patient_id,
                odontologo_id=dentist_id,
                inicio=datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=tz),
                fin=datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=tz),
                motivo="Control",
                estado=EstadoTurno.CONFIRMADO,
                origen=OrigenTurno.ONLINE,
            )
            # Turno 2: Cancelled appointment on 10:00 - 10:30 (CB-03: must release slot)
            t_cancelled = Turno(
                paciente_id=patient_id,
                odontologo_id=dentist_id,
                inicio=datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=tz),
                fin=datetime.datetime.combine(future_monday, datetime.time(10, 30), tzinfo=tz),
                motivo="Cancelado",
                estado=EstadoTurno.CANCELADO,
                origen=OrigenTurno.ONLINE,
            )
            session.add_all([tpl, tpl_cb2, t_active, t_cancelled])
            await session.commit()

    anyio.run(_setup_data)

    # 1. Expected behavior: 09:30-10:00 blocked, 10:00-10:30 free (CB-03), zero patient PII
    res = client.get(
        f"/api/disponibilidad?odontologo_id={dentist_id}&fecha={future_monday.isoformat()}",
        headers=pac_headers,
    )
    assert res.status_code == 200
    slots = res.json()
    assert len(slots) == 3
    # Check slots: 09:00-09:30, 10:00-10:30, 10:30-11:00
    slot_starts = [s["inicio"] for s in slots]
    assert any("09:00:00" in s for s in slot_starts)
    assert not any("09:30:00" in s for s in slot_starts)
    assert any("10:00:00" in s for s in slot_starts)
    assert any("10:30:00" in s for s in slot_starts)

    # Hard Rule #12: Assert zero patient PII in response items
    for s in slots:
        assert "paciente" not in s
        assert "paciente_id" not in s
        assert "dni" not in s
        assert "email" not in s
        assert "nombre" not in s
        assert set(s.keys()) == {"inicio", "fin", "odontologo_id", "prestacion"}

    # 2. CB-02: Remainder incomplete slot omitted (40-min slot in 60-min window returns only 09:00-09:40)
    res_cb2 = client.get(
        f"/api/disponibilidad?odontologo_id={users['odontologo_2'].id}&fecha={future_monday.isoformat()}",
        headers=pac_headers,
    )
    assert res_cb2.status_code == 200
    slots_cb2 = res_cb2.json()
    assert len(slots_cb2) == 1
    assert "09:00:00" in slots_cb2[0]["inicio"]
    assert "09:40:00" in slots_cb2[0]["fin"]

    # 3. Business error: Past date rejected with 422 (RN-GL-02)
    past_date = "2020-01-01"
    res_past = client.get(
        f"/api/disponibilidad?odontologo_id={dentist_id}&fecha={past_date}",
        headers=pac_headers,
    )
    assert res_past.status_code == 422

    # 4. Business error: Non-existent dentist (404 Not Found, CB-06)
    res_missing_dentist = client.get(
        f"/api/disponibilidad?odontologo_id=999999&fecha={future_monday.isoformat()}",
        headers=pac_headers,
    )
    assert res_missing_dentist.status_code == 404

    # 5. Business error: Non-dentist user (422 Unprocessable Entity, CB-06)
    res_patient_dentist = client.get(
        f"/api/disponibilidad?odontologo_id={patient_id}&fecha={future_monday.isoformat()}",
        headers=pac_headers,
    )
    assert res_patient_dentist.status_code == 422
