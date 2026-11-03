import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


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
async def dentist_user(async_session: AsyncSession) -> Usuario:
    dentist = Usuario(
        nombre="Dra. Sofía Martín (Ficticia)",
        email="sofia.martin.ficticia@example.com",
        nro_socio="ODO-FICT-010",
        password_hash="pw_hash_dentist",
        rol=RolUsuario.ODONTOLOGO,
    )
    async_session.add(dentist)
    await async_session.commit()
    await async_session.refresh(dentist)
    return dentist


@pytest.fixture
async def patient_user(async_session: AsyncSession) -> Usuario:
    patient = Usuario(
        nombre="Lucía Gómez (Ficticia)",
        email="lucia.gomez.ficticia@example.com",
        nro_socio="PAC-FICT-025",
        password_hash="pw_hash_patient",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(patient)
    await async_session.commit()
    await async_session.refresh(patient)
    return patient


@pytest.mark.asyncio
async def test_find_overlapping_for_update_active_states_block(
    async_session: AsyncSession,
    dentist_user: Usuario,
    patient_user: Usuario,
):
    """Task 1.1: Active states (solicitado, confirmado, presente, ausente) are returned by find_overlapping_for_update."""
    repo = SqlAlchemyTurnoRepository(session=async_session)
    base_start = datetime.datetime(2027, 5, 3, 9, 30, tzinfo=AR_TZ)
    base_end = datetime.datetime(2027, 5, 3, 10, 0, tzinfo=AR_TZ)

    for idx, active_state in enumerate(
        [EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO, EstadoTurno.PRESENTE, EstadoTurno.AUSENTE]
    ):
        slot_start = base_start + datetime.timedelta(hours=idx)
        slot_end = base_end + datetime.timedelta(hours=idx)
        turno = Turno(
            paciente_id=patient_user.id,
            odontologo_id=dentist_user.id,
            inicio=slot_start,
            fin=slot_end,
            motivo=f"Consulta sintética {idx}",
            estado=active_state,
            origen=OrigenTurno.ONLINE,
        )
        async_session.add(turno)
        await async_session.commit()

        # Exact match
        overlaps = await repo.find_overlapping_for_update(
            odontologo_id=dentist_user.id,
            inicio=slot_start,
            fin=slot_end,
        )
        assert len(overlaps) == 1
        assert overlaps[0].estado == active_state

        # Partial overlap (CB-04): [slot_start + 15m, slot_end + 15m)
        partial_overlaps = await repo.find_overlapping_for_update(
            odontologo_id=dentist_user.id,
            inicio=slot_start + datetime.timedelta(minutes=15),
            fin=slot_end + datetime.timedelta(minutes=15),
        )
        assert len(partial_overlaps) == 1


@pytest.mark.asyncio
async def test_find_overlapping_for_update_cancelled_and_adjacent_allowed(
    async_session: AsyncSession,
    dentist_user: Usuario,
    patient_user: Usuario,
):
    """Task 1.1: Cancelled/annulled appointments (CB-03) and adjacent intervals fin_A == inicio_B (CB-01) do not block."""
    repo = SqlAlchemyTurnoRepository(session=async_session)
    slot_start = datetime.datetime(2027, 5, 3, 9, 0, tzinfo=AR_TZ)
    slot_end = datetime.datetime(2027, 5, 3, 9, 30, tzinfo=AR_TZ)

    # Insert a CANCELADO and an ANULADO appointment in the exact same slot
    for released_state in (EstadoTurno.CANCELADO, EstadoTurno.ANULADO):
        async_session.add(
            Turno(
                paciente_id=patient_user.id,
                odontologo_id=dentist_user.id,
                inicio=slot_start,
                fin=slot_end,
                motivo="Turno liberado sintético",
                estado=released_state,
                origen=OrigenTurno.ONLINE,
            )
        )
    # Insert an active appointment in [09:00, 09:30)
    active_turno = Turno(
        paciente_id=patient_user.id,
        odontologo_id=dentist_user.id,
        inicio=slot_start,
        fin=slot_end,
        motivo="Turno activo 09:00-09:30",
        estado=EstadoTurno.SOLICITADO,
        origen=OrigenTurno.ONLINE,
    )
    async_session.add(active_turno)
    await async_session.commit()
    await async_session.refresh(active_turno)

    # Excluding active_turno leaves only CANCELADO and ANULADO -> 0 overlaps (CB-03)
    released_check = await repo.find_overlapping_for_update(
        odontologo_id=dentist_user.id,
        inicio=slot_start,
        fin=slot_end,
        exclude_turno_id=active_turno.id,
    )
    assert released_check == []

    # CB-01: Contiguous after [09:30, 10:00) where fin_A == inicio_B -> 0 overlaps
    adjacent_after = await repo.find_overlapping_for_update(
        odontologo_id=dentist_user.id,
        inicio=datetime.datetime(2027, 5, 3, 9, 30, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 5, 3, 10, 0, tzinfo=AR_TZ),
    )
    assert adjacent_after == []

    # CB-01: Contiguous before [08:30, 09:00) where fin_B == inicio_A -> 0 overlaps
    adjacent_before = await repo.find_overlapping_for_update(
        odontologo_id=dentist_user.id,
        inicio=datetime.datetime(2027, 5, 3, 8, 30, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 5, 3, 9, 0, tzinfo=AR_TZ),
    )
    assert adjacent_before == []


def test_validate_slot_matches_template_valid_and_timezone_normalization():
    """Task 2.1: Pure sync validator accepts exact template grid slot and normalizes to clinic timezone."""
    from app.application.turnos import validate_slot_matches_template

    monday_template = PlantillaDisponibilidad(
        id=1,
        odontologo_id=10,
        dia_semana=0,  # Monday
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(11, 0),
        duracion_slot_minutos=30,
        prestacion="Consulta general",
    )
    now_ref = datetime.datetime(2027, 5, 3, 8, 0, tzinfo=AR_TZ)  # Monday 08:00 (-03:00)

    # Pass UTC timestamps corresponding to 09:30-10:00 in Buenos Aires (12:30-13:00 UTC)
    utc_start = datetime.datetime(2027, 5, 3, 12, 30, tzinfo=datetime.timezone.utc)
    utc_end = datetime.datetime(2027, 5, 3, 13, 0, tzinfo=datetime.timezone.utc)

    inicio_local, fin_local = validate_slot_matches_template(
        inicio=utc_start,
        fin=utc_end,
        templates=[monday_template],
        timezone_str="America/Argentina/Buenos_Aires",
        now_override=now_ref,
    )
    assert inicio_local == datetime.datetime(2027, 5, 3, 9, 30, tzinfo=AR_TZ)
    assert fin_local == datetime.datetime(2027, 5, 3, 10, 0, tzinfo=AR_TZ)


def test_validate_slot_matches_template_rejects_past_elapsed_and_off_grid():
    """Task 2.1: Rejects past dates (RN-GL-02), elapsed same-day slots (CB-05), off-template hours (RN-AG-02), and incomplete remainders (CB-02)."""
    from app.application.turnos import validate_slot_matches_template

    wednesday_40m_template = PlantillaDisponibilidad(
        id=2,
        odontologo_id=10,
        dia_semana=2,  # Wednesday
        hora_inicio=datetime.time(9, 0),
        hora_fin=datetime.time(10, 0),
        duracion_slot_minutos=40,
        prestacion="Endodoncia",
    )
    # Current clinic clock: Wednesday 2027-05-05 at 09:15 (-03:00)
    now_ref = datetime.datetime(2027, 5, 5, 9, 15, tzinfo=AR_TZ)

    # 1. Past date (2027-04-28 Wednesday) -> ValueError (RN-GL-02)
    with pytest.raises(ValueError, match="pasad"):
        validate_slot_matches_template(
            inicio=datetime.datetime(2027, 4, 28, 9, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 4, 28, 9, 40, tzinfo=AR_TZ),
            templates=[wednesday_40m_template],
            timezone_str="America/Argentina/Buenos_Aires",
            now_override=now_ref,
        )

    # 2. Same-day already elapsed slot (09:00 <= 09:15 on 2027-05-05) -> ValueError (CB-05)
    with pytest.raises(ValueError, match="transcurrido|pasad"):
        validate_slot_matches_template(
            inicio=datetime.datetime(2027, 5, 5, 9, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 5, 5, 9, 40, tzinfo=AR_TZ),
            templates=[wednesday_40m_template],
            timezone_str="America/Argentina/Buenos_Aires",
            now_override=now_ref,
        )

    # 3. Future Wednesday (2027-05-12): incomplete 20-minute remainder 09:40-10:00 -> ValueError (CB-02)
    with pytest.raises(ValueError, match="plantilla|slot"):
        validate_slot_matches_template(
            inicio=datetime.datetime(2027, 5, 12, 9, 40, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 5, 12, 10, 0, tzinfo=AR_TZ),
            templates=[wednesday_40m_template],
            timezone_str="America/Argentina/Buenos_Aires",
            now_override=now_ref,
        )

    # 4. Future Wednesday (2027-05-12): misaligned start 09:10-09:50 -> ValueError (CB-02)
    with pytest.raises(ValueError, match="plantilla|slot"):
        validate_slot_matches_template(
            inicio=datetime.datetime(2027, 5, 12, 9, 10, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 5, 12, 9, 50, tzinfo=AR_TZ),
            templates=[wednesday_40m_template],
            timezone_str="America/Argentina/Buenos_Aires",
            now_override=now_ref,
        )

    # 5. Future Wednesday (2027-05-12): outside template hours 14:00-14:40 -> ValueError (RN-AG-02)
    with pytest.raises(ValueError, match="plantilla|slot"):
        validate_slot_matches_template(
            inicio=datetime.datetime(2027, 5, 12, 14, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 5, 12, 14, 40, tzinfo=AR_TZ),
            templates=[wednesday_40m_template],
            timezone_str="America/Argentina/Buenos_Aires",
            now_override=now_ref,
        )


def test_turno_create_and_response_schemas_strict_validation():
    """Task 3.1: TurnoCreate and TurnoResponse enforce extra='forbid', str_strip_whitespace, motivo bounds, and fin > inicio."""
    from pydantic import ValidationError
    from app.api.turnos import TurnoCreate, TurnoResponse

    valid_start = datetime.datetime(2027, 5, 3, 9, 30, tzinfo=AR_TZ)
    valid_end = datetime.datetime(2027, 5, 3, 10, 0, tzinfo=AR_TZ)

    # 1. Valid payload strips whitespace on motivo
    valid = TurnoCreate(
        odontologo_id=10,
        inicio=valid_start,
        fin=valid_end,
        motivo="  Control anual y limpieza  ",
    )
    assert valid.motivo == "Control anual y limpieza"

    # 2. Reject undeclared fields (Hard Rule #1 & OWASP BOLA/Mass Assignment protection)
    for forbidden_field in ({"paciente_id": 99}, {"estado": "confirmado"}, {"origen": "manual"}, {"box": 1}):
        with pytest.raises(ValidationError):
            TurnoCreate(
                odontologo_id=10,
                inicio=valid_start,
                fin=valid_end,
                motivo="Control general",
                **forbidden_field,
            )

    # 3. Reject whitespace-only motivo
    with pytest.raises(ValidationError):
        TurnoCreate(
            odontologo_id=10,
            inicio=valid_start,
            fin=valid_end,
            motivo="     ",
        )

    # 4. Reject fin <= inicio (including mixed naive + aware datetimes without raising 500 TypeError)
    with pytest.raises(ValidationError):
        TurnoCreate(
            odontologo_id=10,
            inicio=valid_start,
            fin=valid_start,
            motivo="Control general",
        )

    with pytest.raises(ValidationError):
        TurnoCreate(
            odontologo_id=10,
            inicio=datetime.datetime(2027, 5, 3, 10, 0, tzinfo=AR_TZ),
            fin=datetime.datetime(2027, 5, 3, 9, 30),  # naive datetime mixed with aware
            motivo="Control general",
        )

    # 5. TurnoResponse also enforces extra="forbid"
    with pytest.raises(ValidationError):
        TurnoResponse(
            id=1,
            paciente_id=25,
            odontologo_id=10,
            inicio=valid_start,
            fin=valid_end,
            motivo="Control general",
            estado=EstadoTurno.SOLICITADO,
            origen=OrigenTurno.ONLINE,
            creado_en=valid_start,
            actualizado_en=valid_start,
            campo_extra="invalido",  # type: ignore[call-arg]
        )


def _next_weekday(start_date: datetime.date, target_weekday: int) -> datetime.date:
    """Returns the next strictly future date matching target_weekday (0=Monday..6=Sunday)."""
    days_ahead = (target_weekday - start_date.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + datetime.timedelta(days=days_ahead)


@pytest.fixture
def client_and_context():
    import anyio
    from starlette.testclient import TestClient

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
                    nro_socio="SOC-FICT-101",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_martin = Usuario(
                    nombre="Martín Pérez (Ficticio)",
                    email="martin.perez.ficticio@example.com",
                    nro_socio="SOC-FICT-102",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_pendiente = Usuario(
                    nombre="Carla Ruiz (Ficticia)",
                    email="carla.ruiz.ficticia@example.com",
                    nro_socio="SOC-FICT-103",
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
                odontologo = Usuario(
                    nombre="Dra. Sofía Martín (Ficticia)",
                    email="sofia.martin.ficticia@example.com",
                    nro_socio="ODO-FICT-201",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                session.add_all(
                    [paciente_lucia, paciente_martin, paciente_pendiente, recepcion, odontologo]
                )
                await session.commit()
                for u in (paciente_lucia, paciente_martin, paciente_pendiente, recepcion, odontologo):
                    await session.refresh(u)

                # Seed templates for Dra. Sofía Martín:
                # 1) Monday (0): 09:00-11:00, 30 min slots
                # 2) Wednesday (2): 09:00-10:00, 40 min slots (for CB-02 remainder test)
                tpl_monday = PlantillaDisponibilidad(
                    odontologo_id=odontologo.id,
                    dia_semana=0,
                    hora_inicio=datetime.time(9, 0),
                    hora_fin=datetime.time(11, 0),
                    duracion_slot_minutos=30,
                    prestacion="Consulta general",
                )
                tpl_wednesday = PlantillaDisponibilidad(
                    odontologo_id=odontologo.id,
                    dia_semana=2,
                    hora_inicio=datetime.time(9, 0),
                    hora_fin=datetime.time(10, 0),
                    duracion_slot_minutos=40,
                    prestacion="Endodoncia",
                )
                session.add_all([tpl_monday, tpl_wednesday])
                await session.commit()

                return {
                    "paciente_lucia": paciente_lucia,
                    "paciente_martin": paciente_martin,
                    "paciente_pendiente": paciente_pendiente,
                    "recepcion": recepcion,
                    "odontologo": odontologo,
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


def test_post_turnos_happy_path_and_removes_slot_from_disponibilidad(client_and_context):
    """Task 3.2 (Scenario 1.1): Patient books free slot -> 201 Created, estado=solicitado, origen=online, slot removed from GET /api/disponibilidad."""
    client, _app, users, tokens = client_and_context
    odontologo_id = users["odontologo"].id
    paciente_id = users["paciente_lucia"].id
    headers = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}

    today_local = datetime.datetime.now(AR_TZ).date()
    future_monday = _next_weekday(today_local, 0)
    slot_start = datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=AR_TZ)
    slot_end = datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=AR_TZ)

    response = client.post(
        "/api/turnos",
        headers=headers,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_start.isoformat(),
            "fin": slot_end.isoformat(),
            "motivo": "Control anual y limpieza",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"] > 0
    assert data["paciente_id"] == paciente_id
    assert data["odontologo_id"] == odontologo_id
    assert data["estado"] == "solicitado"
    assert data["origen"] == "online"
    assert data["motivo"] == "Control anual y limpieza"

    # Verify GET /api/disponibilidad no longer offers 09:30-10:00 (US-003 CA-3)
    disp_res = client.get(
        f"/api/disponibilidad?odontologo_id={odontologo_id}&fecha={future_monday.isoformat()}",
        headers=headers,
    )
    assert disp_res.status_code == 200
    free_starts = [
        datetime.datetime.fromisoformat(s["inicio"]).astimezone(AR_TZ).time()
        for s in disp_res.json()
    ]
    assert datetime.time(9, 30) not in free_starts
    assert datetime.time(9, 0) in free_starts
    assert datetime.time(10, 0) in free_starts


def test_post_turnos_overlap_cancelled_and_contiguous_scenarios(client_and_context):
    """Task 3.2 (Scenarios 2.1, 2.2, 2.3): Active overlap -> 409 Conflict (RN-AG-01); cancelado/anulado -> 201 (CB-03); adjacent fin_A == inicio_B -> 201 (CB-01)."""
    import anyio

    client, app, users, tokens = client_and_context
    odontologo_id = users["odontologo"].id
    headers_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    headers_martin = {"Authorization": f"Bearer {tokens['paciente_martin']}"}

    today_local = datetime.datetime.now(AR_TZ).date()
    future_monday = _next_weekday(today_local, 0)
    slot_0900 = datetime.datetime.combine(future_monday, datetime.time(9, 0), tzinfo=AR_TZ)
    slot_0930 = datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=AR_TZ)
    slot_1000 = datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=AR_TZ)

    # 1. Lucía books 09:00-09:30 -> 201 Created
    res1 = client.post(
        "/api/turnos",
        headers=headers_lucia,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900.isoformat(),
            "fin": slot_0930.isoformat(),
            "motivo": "Primera consulta",
        },
    )
    assert res1.status_code == 201
    turno_1_id = res1.json()["id"]

    # 2. Scenario 2.1 (RN-AG-01, CB-04): Martín tries to book the same 09:00-09:30 slot -> 409 Conflict
    res_conflict = client.post(
        "/api/turnos",
        headers=headers_martin,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900.isoformat(),
            "fin": slot_0930.isoformat(),
            "motivo": "Intento superpuesto",
        },
    )
    assert res_conflict.status_code == 409

    # 3. Scenario 2.3 (CB-01): Martín books contiguous slot 09:30-10:00 (fin_A == inicio_B) -> 201 Created
    res_adjacent = client.post(
        "/api/turnos",
        headers=headers_martin,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0930.isoformat(),
            "fin": slot_1000.isoformat(),
            "motivo": "Turno contiguo inmediato",
        },
    )
    assert res_adjacent.status_code == 201

    # 4. Scenario 2.2 (CB-03, RN-TU-04): Mark 09:00-09:30 as CANCELADO in DB, then re-book -> 201 Created
    async def _mark_cancelled():
        async with app.state.session_factory() as session:
            t = await session.get(Turno, turno_1_id)
            assert t is not None
            t.estado = EstadoTurno.CANCELADO
            await session.commit()

    anyio.run(_mark_cancelled)

    res_rebook = client.post(
        "/api/turnos",
        headers=headers_martin,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900.isoformat(),
            "fin": slot_0930.isoformat(),
            "motivo": "Reserva sobre hueco liberado por cancelación",
        },
    )
    assert res_rebook.status_code == 201


def test_post_turnos_template_and_timezone_validations(client_and_context):
    """Task 3.2 (Scenarios 3.1, 3.2, 3.3): Rejects outside template (RN-AG-02), incomplete remainder (CB-02), and past/elapsed slots (RN-GL-02, CB-05)."""
    client, _app, users, tokens = client_and_context
    odontologo_id = users["odontologo"].id
    headers = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}

    now_local = datetime.datetime.now(AR_TZ)
    today_local = now_local.date()
    future_monday = _next_weekday(today_local, 0)
    future_wednesday = _next_weekday(today_local, 2)

    # 1. Scenario 3.1 (RN-AG-02): Outside Monday template hours (14:00-14:30) -> 422
    res_out_hours = client.post(
        "/api/turnos",
        headers=headers,
        json={
            "odontologo_id": odontologo_id,
            "inicio": datetime.datetime.combine(future_monday, datetime.time(14, 0), tzinfo=AR_TZ).isoformat(),
            "fin": datetime.datetime.combine(future_monday, datetime.time(14, 30), tzinfo=AR_TZ).isoformat(),
            "motivo": "Fuera de horario de plantilla",
        },
    )
    assert res_out_hours.status_code == 422

    # 2. Scenario 3.2 (CB-02): Wednesday 09:00-10:00 (40m slots) -> 09:40-10:00 remainder rejected with 422
    res_remainder = client.post(
        "/api/turnos",
        headers=headers,
        json={
            "odontologo_id": odontologo_id,
            "inicio": datetime.datetime.combine(future_wednesday, datetime.time(9, 40), tzinfo=AR_TZ).isoformat(),
            "fin": datetime.datetime.combine(future_wednesday, datetime.time(10, 0), tzinfo=AR_TZ).isoformat(),
            "motivo": "Remanente incompleto de 20 min",
        },
    )
    assert res_remainder.status_code == 422

    # 3. Scenario 3.3 (RN-GL-02): Past date -> 422
    past_monday = today_local - datetime.timedelta(days=7)
    res_past = client.post(
        "/api/turnos",
        headers=headers,
        json={
            "odontologo_id": odontologo_id,
            "inicio": datetime.datetime.combine(past_monday, datetime.time(9, 0), tzinfo=AR_TZ).isoformat(),
            "fin": datetime.datetime.combine(past_monday, datetime.time(9, 30), tzinfo=AR_TZ).isoformat(),
            "motivo": "Fecha pasada",
        },
    )
    assert res_past.status_code == 422

    # 4. Scenario 3.3 / CB-05 at HTTP boundary: Same-day already elapsed slot (00:00-00:30 today) -> 422
    import anyio

    async def _seed_today_early_template():
        async with _app.state.session_factory() as session:
            session.add(
                PlantillaDisponibilidad(
                    odontologo_id=odontologo_id,
                    dia_semana=today_local.weekday(),
                    hora_inicio=datetime.time(0, 0),
                    hora_fin=datetime.time(0, 30),
                    duracion_slot_minutos=30,
                    prestacion="Guardia madrugada",
                )
            )
            await session.commit()

    anyio.run(_seed_today_early_template)

    res_elapsed_today = client.post(
        "/api/turnos",
        headers=headers,
        json={
            "odontologo_id": odontologo_id,
            "inicio": datetime.datetime.combine(today_local, datetime.time(0, 0), tzinfo=AR_TZ).isoformat(),
            "fin": datetime.datetime.combine(today_local, datetime.time(0, 30), tzinfo=AR_TZ).isoformat(),
            "motivo": "Slot ya transcurrido hoy",
        },
    )
    assert res_elapsed_today.status_code == 422


def test_post_turnos_rbac_dentist_and_payload_errors(client_and_context):
    """Task 3.2 (Scenarios 4.1, 4.2, 4.3): Validates RBAC (401/403), dentist existence/role (404/422 CB-06), and payload rules (422)."""
    client, _app, users, tokens = client_and_context
    odontologo_id = users["odontologo"].id
    headers_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}

    today_local = datetime.datetime.now(AR_TZ).date()
    future_monday = _next_weekday(today_local, 0)
    slot_start = datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=AR_TZ).isoformat()
    slot_end = datetime.datetime.combine(future_monday, datetime.time(10, 30), tzinfo=AR_TZ).isoformat()
    valid_body = {
        "odontologo_id": odontologo_id,
        "inicio": slot_start,
        "fin": slot_end,
        "motivo": "Consulta de control",
    }

    # 1. Unauthenticated -> 401
    assert client.post("/api/turnos", json=valid_body).status_code == 401

    # 2. Scenario 4.2: Recepción or Odontólogo role -> 403 Forbidden (RN-TU-01, RN-GL-01)
    for role_key in ("recepcion", "odontologo"):
        res_forbidden = client.post(
            "/api/turnos",
            headers={"Authorization": f"Bearer {tokens[role_key]}"},
            json=valid_body,
        )
        assert res_forbidden.status_code == 403

    # 3. Scenario 4.2: Paciente with debe_cambiar_password=True -> 403 password_change_required (US-010)
    res_pw_pending = client.post(
        "/api/turnos",
        headers={"Authorization": f"Bearer {tokens['paciente_pendiente']}"},
        json=valid_body,
    )
    assert res_pw_pending.status_code == 403
    assert res_pw_pending.json()["detail"] == "password_change_required"

    # 4. Scenario 4.1 (CB-06): Non-existent odontologo_id -> 404 Not Found
    res_404 = client.post(
        "/api/turnos",
        headers=headers_lucia,
        json={**valid_body, "odontologo_id": 99999},
    )
    assert res_404.status_code == 404

    # 5. Scenario 4.1 (CB-06): Target user exists but is not odontologo (e.g., recepcion) -> 422
    res_not_dentist = client.post(
        "/api/turnos",
        headers=headers_lucia,
        json={**valid_body, "odontologo_id": users["recepcion"].id},
    )
    assert res_not_dentist.status_code == 422

    # 6. Scenario 4.3: Undeclared field (extra="forbid") or empty motivo -> 422
    res_extra = client.post(
        "/api/turnos",
        headers=headers_lucia,
        json={**valid_body, "paciente_id": 999},
    )
    assert res_extra.status_code == 422

    res_empty_motivo = client.post(
        "/api/turnos",
        headers=headers_lucia,
        json={**valid_body, "motivo": "   "},
    )
    assert res_empty_motivo.status_code == 422



