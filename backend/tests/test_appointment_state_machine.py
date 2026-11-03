import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models.base import Base
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
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
        nro_socio="ODO-FICT-101",
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
        nro_socio="PAC-FICT-101",
        password_hash="pw_hash_patient",
        rol=RolUsuario.PACIENTE,
    )
    async_session.add(patient)
    await async_session.commit()
    await async_session.refresh(patient)
    return patient


@pytest.mark.asyncio
async def test_get_by_id_for_update_returns_persisted_turno(
    async_session: AsyncSession,
    dentist_user: Usuario,
    patient_user: Usuario,
):
    """Task 1.1: get_by_id_for_update returns the persisted Turno when the ID exists."""
    repo = SqlAlchemyTurnoRepository(session=async_session)
    inicio = datetime.datetime(2027, 6, 7, 9, 0, tzinfo=AR_TZ)
    fin = datetime.datetime(2027, 6, 7, 9, 30, tzinfo=AR_TZ)

    turno = Turno(
        paciente_id=patient_user.id,
        odontologo_id=dentist_user.id,
        inicio=inicio,
        fin=fin,
        motivo="Control general sintético",
        estado=EstadoTurno.SOLICITADO,
        origen=OrigenTurno.ONLINE,
    )
    async_session.add(turno)
    await async_session.commit()
    await async_session.refresh(turno)

    fetched = await repo.get_by_id_for_update(turno.id)
    assert fetched is not None
    assert fetched.id == turno.id
    assert fetched.paciente_id == patient_user.id
    assert fetched.odontologo_id == dentist_user.id
    assert fetched.estado == EstadoTurno.SOLICITADO


@pytest.mark.asyncio
async def test_get_by_id_for_update_returns_none_for_missing_id(
    async_session: AsyncSession,
    dentist_user: Usuario,
    patient_user: Usuario,
):
    """Task 1.1: get_by_id_for_update returns None when the ID does not exist and isolates among multiple rows."""
    repo = SqlAlchemyTurnoRepository(session=async_session)
    assert await repo.get_by_id_for_update(999999) is None

    t1 = Turno(
        paciente_id=patient_user.id,
        odontologo_id=dentist_user.id,
        inicio=datetime.datetime(2027, 6, 8, 9, 0, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 6, 8, 9, 30, tzinfo=AR_TZ),
        motivo="Turno sintético 1",
        estado=EstadoTurno.SOLICITADO,
        origen=OrigenTurno.ONLINE,
    )
    t2 = Turno(
        paciente_id=patient_user.id,
        odontologo_id=dentist_user.id,
        inicio=datetime.datetime(2027, 6, 8, 9, 30, tzinfo=AR_TZ),
        fin=datetime.datetime(2027, 6, 8, 10, 0, tzinfo=AR_TZ),
        motivo="Turno sintético 2",
        estado=EstadoTurno.CONFIRMADO,
        origen=OrigenTurno.MANUAL,
    )
    async_session.add_all([t1, t2])
    await async_session.commit()

    fetched_2 = await repo.get_by_id_for_update(t2.id)
    assert fetched_2 is not None
    assert fetched_2.id == t2.id
    assert fetched_2.motivo == "Turno sintético 2"
    assert fetched_2.estado == EstadoTurno.CONFIRMADO


# =====================================================================
# Task 2.1: Pure Synchronous State Machine & Anticipation Validator
# =====================================================================


def test_validate_state_transition_is_pure_synchronous_function():
    """Task 2.1 (Hard Rule #3): validate_state_transition must be a pure synchronous def function."""
    import inspect
    from app.application.turnos import validate_state_transition

    assert inspect.isfunction(validate_state_transition)
    assert not inspect.iscoroutinefunction(validate_state_transition)


def test_validate_state_transition_role_allowlist_and_ownership_bola():
    """Task 2.1: Role allowlist and ownership checks raise UnauthorizedTransitionError (403) before state/time checks."""
    from app.application.turnos import (
        UnauthorizedTransitionError,
        validate_state_transition,
    )

    now = datetime.datetime(2027, 6, 7, 10, 0, tzinfo=AR_TZ)
    # Even if start time is < 24h (e.g. 2h away) or state is terminal (PRESENTE),
    # role and ownership checks MUST take precedence and raise UnauthorizedTransitionError (403).
    inicio_soon = now + datetime.timedelta(hours=2)

    # 1. PACIENTE cannot set confirmado, anulado, presente, ausente, or solicitado
    for forbidden_target in (
        EstadoTurno.CONFIRMADO,
        EstadoTurno.ANULADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
        EstadoTurno.SOLICITADO,
    ):
        with pytest.raises(UnauthorizedTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.PACIENTE,
                actor_user_id=10,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=EstadoTurno.SOLICITADO,
                nuevo_estado=forbidden_target,
                turno_inicio=inicio_soon,
                now_local=now,
            )

    # 2. RECEPCION cannot set cancelado, presente, ausente, or solicitado
    for forbidden_target in (
        EstadoTurno.CANCELADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
        EstadoTurno.SOLICITADO,
    ):
        with pytest.raises(UnauthorizedTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.RECEPCION,
                actor_user_id=99,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=EstadoTurno.CONFIRMADO,
                nuevo_estado=forbidden_target,
                turno_inicio=inicio_soon,
                now_local=now,
            )

    # 3. ODONTOLOGO cannot set confirmado, anulado, cancelado, or solicitado
    for forbidden_target in (
        EstadoTurno.CONFIRMADO,
        EstadoTurno.ANULADO,
        EstadoTurno.CANCELADO,
        EstadoTurno.SOLICITADO,
    ):
        with pytest.raises(UnauthorizedTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.ODONTOLOGO,
                actor_user_id=20,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=EstadoTurno.SOLICITADO,
                nuevo_estado=forbidden_target,
                turno_inicio=inicio_soon,
                now_local=now,
            )

    # 4. BOLA/Ownership: PACIENTE attempting to cancel another patient's appointment -> UnauthorizedTransitionError
    # Even when the appointment is in a terminal state (PRESENTE) and < 24h away, BOLA must fail with 403 first.
    with pytest.raises(UnauthorizedTransitionError):
        validate_state_transition(
            actor_rol=RolUsuario.PACIENTE,
            actor_user_id=999,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=EstadoTurno.PRESENTE,
            nuevo_estado=EstadoTurno.CANCELADO,
            turno_inicio=inicio_soon,
            now_local=now,
        )

    # 5. BOLA/Ownership: ODONTOLOGO attempting to mark another dentist's appointment -> UnauthorizedTransitionError
    for target in (EstadoTurno.PRESENTE, EstadoTurno.AUSENTE):
        with pytest.raises(UnauthorizedTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.ODONTOLOGO,
                actor_user_id=888,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=EstadoTurno.SOLICITADO,
                nuevo_estado=target,
                turno_inicio=inicio_soon,
                now_local=now,
            )


def test_validate_state_transition_valid_and_invalid_source_states():
    """Task 2.1: Valid transitions succeed and invalid source states raise InvalidStateTransitionError (409)."""
    from app.application.turnos import (
        InvalidStateTransitionError,
        validate_state_transition,
    )

    now = datetime.datetime(2027, 6, 7, 10, 0, tzinfo=AR_TZ)
    inicio_48h = now + datetime.timedelta(hours=48)

    # Valid transitions:
    # - Recepcion: solicitado -> confirmado, solicitado -> anulado, confirmado -> anulado
    validate_state_transition(
        actor_rol=RolUsuario.RECEPCION,
        actor_user_id=1,
        turno_paciente_id=10,
        turno_odontologo_id=20,
        estado_actual=EstadoTurno.SOLICITADO,
        nuevo_estado=EstadoTurno.CONFIRMADO,
        turno_inicio=inicio_48h,
        now_local=now,
    )
    for source in (EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO):
        validate_state_transition(
            actor_rol=RolUsuario.RECEPCION,
            actor_user_id=1,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=source,
            nuevo_estado=EstadoTurno.ANULADO,
            turno_inicio=inicio_48h,
            now_local=now,
        )

    # - Paciente (owner): solicitado -> cancelado, confirmado -> cancelado
    for source in (EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO):
        validate_state_transition(
            actor_rol=RolUsuario.PACIENTE,
            actor_user_id=10,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=source,
            nuevo_estado=EstadoTurno.CANCELADO,
            turno_inicio=inicio_48h,
            now_local=now,
        )

    # - Odontologo (assigned): confirmado -> presente | ausente
    for target in (EstadoTurno.PRESENTE, EstadoTurno.AUSENTE):
        validate_state_transition(
            actor_rol=RolUsuario.ODONTOLOGO,
            actor_user_id=20,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=EstadoTurno.CONFIRMADO,
            nuevo_estado=target,
            turno_inicio=inicio_48h,
            now_local=now,
        )

    # Invalid source states -> InvalidStateTransitionError (409):
    # - Recepcion confirming from non-solicitado states
    for invalid_source in (
        EstadoTurno.CONFIRMADO,
        EstadoTurno.CANCELADO,
        EstadoTurno.ANULADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
    ):
        with pytest.raises(InvalidStateTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.RECEPCION,
                actor_user_id=1,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=invalid_source,
                nuevo_estado=EstadoTurno.CONFIRMADO,
                turno_inicio=inicio_48h,
                now_local=now,
            )

    # - Recepcion annulling from terminal states
    for invalid_source in (
        EstadoTurno.CANCELADO,
        EstadoTurno.ANULADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
    ):
        with pytest.raises(InvalidStateTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.RECEPCION,
                actor_user_id=1,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=invalid_source,
                nuevo_estado=EstadoTurno.ANULADO,
                turno_inicio=inicio_48h,
                now_local=now,
            )

    # - Paciente cancelling from terminal states
    for invalid_source in (
        EstadoTurno.CANCELADO,
        EstadoTurno.ANULADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
    ):
        with pytest.raises(InvalidStateTransitionError):
            validate_state_transition(
                actor_rol=RolUsuario.PACIENTE,
                actor_user_id=10,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=invalid_source,
                nuevo_estado=EstadoTurno.CANCELADO,
                turno_inicio=inicio_48h,
                now_local=now,
            )

    # - Odontologo marking presente/ausente from non-confirmado states (including solicitado!)
    for invalid_source in (
        EstadoTurno.SOLICITADO,
        EstadoTurno.CANCELADO,
        EstadoTurno.ANULADO,
        EstadoTurno.PRESENTE,
        EstadoTurno.AUSENTE,
    ):
        for target in (EstadoTurno.PRESENTE, EstadoTurno.AUSENTE):
            with pytest.raises(InvalidStateTransitionError):
                validate_state_transition(
                    actor_rol=RolUsuario.ODONTOLOGO,
                    actor_user_id=20,
                    turno_paciente_id=10,
                    turno_odontologo_id=20,
                    estado_actual=invalid_source,
                    nuevo_estado=target,
                    turno_inicio=inicio_48h,
                    now_local=now,
                )


def test_validate_state_transition_anticipation_and_timezone_boundaries():
    """Task 2.1: Exact 24h boundary passes, 23h59m59s fails (422), past confirmation fails (422), naive SQLite dt works."""
    from app.application.turnos import (
        AnticipationWindowError,
        validate_state_transition,
    )

    now = datetime.datetime(2027, 6, 7, 10, 0, 0, tzinfo=AR_TZ)
    exact_24h = now + datetime.timedelta(hours=24)
    one_sec_short = now + datetime.timedelta(hours=24) - datetime.timedelta(seconds=1)

    # Exact 24h boundary passes for both paciente (cancelado) and recepcion (anulado)
    validate_state_transition(
        actor_rol=RolUsuario.PACIENTE,
        actor_user_id=10,
        turno_paciente_id=10,
        turno_odontologo_id=20,
        estado_actual=EstadoTurno.CONFIRMADO,
        nuevo_estado=EstadoTurno.CANCELADO,
        turno_inicio=exact_24h,
        cancel_min_hours=24,
        now_local=now,
    )
    validate_state_transition(
        actor_rol=RolUsuario.RECEPCION,
        actor_user_id=1,
        turno_paciente_id=10,
        turno_odontologo_id=20,
        estado_actual=EstadoTurno.SOLICITADO,
        nuevo_estado=EstadoTurno.ANULADO,
        turno_inicio=exact_24h,
        cancel_min_hours=24,
        now_local=now,
    )

    # 23h 59m 59s raises AnticipationWindowError
    with pytest.raises(AnticipationWindowError):
        validate_state_transition(
            actor_rol=RolUsuario.PACIENTE,
            actor_user_id=10,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=EstadoTurno.SOLICITADO,
            nuevo_estado=EstadoTurno.CANCELADO,
            turno_inicio=one_sec_short,
            cancel_min_hours=24,
            now_local=now,
        )

    with pytest.raises(AnticipationWindowError):
        validate_state_transition(
            actor_rol=RolUsuario.RECEPCION,
            actor_user_id=1,
            turno_paciente_id=10,
            turno_odontologo_id=20,
            estado_actual=EstadoTurno.CONFIRMADO,
            nuevo_estado=EstadoTurno.ANULADO,
            turno_inicio=one_sec_short,
            cancel_min_hours=24,
            now_local=now,
        )

    # Confirming an appointment at or before now raises AnticipationWindowError (RN-GL-02)
    for past_or_now in (now, now - datetime.timedelta(minutes=30)):
        with pytest.raises(AnticipationWindowError):
            validate_state_transition(
                actor_rol=RolUsuario.RECEPCION,
                actor_user_id=1,
                turno_paciente_id=10,
                turno_odontologo_id=20,
                estado_actual=EstadoTurno.SOLICITADO,
                nuevo_estado=EstadoTurno.CONFIRMADO,
                turno_inicio=past_or_now,
                now_local=now,
            )

    # Naive datetime hydrated by SQLite vs aware now_override normalizes cleanly without TypeError
    naive_future_25h = datetime.datetime(2027, 6, 8, 11, 0, 0)  # naive
    validate_state_transition(
        actor_rol=RolUsuario.PACIENTE,
        actor_user_id=10,
        turno_paciente_id=10,
        turno_odontologo_id=20,
        estado_actual=EstadoTurno.SOLICITADO,
        nuevo_estado=EstadoTurno.CANCELADO,
        turno_inicio=naive_future_25h,
        cancel_min_hours=24,
        now_local=now,
    )


# =====================================================================
# Task 3.1: TurnoEstadoUpdate Schema & PATCH /api/turnos/{id} Endpoint
# =====================================================================


def test_turno_estado_update_schema_strict_validation():
    """Task 3.1 (Hard Rule #1): TurnoEstadoUpdate enforces extra='forbid' and valid EstadoTurno values."""
    from pydantic import ValidationError
    from app.api.turnos import TurnoEstadoUpdate

    valid = TurnoEstadoUpdate(estado=EstadoTurno.CANCELADO)
    assert valid.estado == EstadoTurno.CANCELADO

    # Reject extra undeclared fields (Hard Rule #1 & OWASP Mass Assignment)
    for extra_field in ({"paciente_id": 99}, {"motivo": "cambio"}, {"odontologo_id": 1}):
        with pytest.raises(ValidationError):
            TurnoEstadoUpdate(estado=EstadoTurno.CANCELADO, **extra_field)

    # Reject invalid state string
    with pytest.raises(ValidationError):
        TurnoEstadoUpdate(estado="reprogramado")  # type: ignore[arg-type]


def _next_weekday(start_date: datetime.date, target_weekday: int) -> datetime.date:
    days_ahead = (target_weekday - start_date.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + datetime.timedelta(days=days_ahead)


@pytest.fixture
def state_machine_client_and_context():
    import anyio
    from starlette.testclient import TestClient

    from app.domain.models.plantilla import PlantillaDisponibilidad
    from app.infrastructure.config import Settings
    from app.infrastructure.security import create_access_token, hash_password
    from app.main import create_app

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="supersecret_jwt_key_at_least_32_characters_long!",
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
                paciente_lucia = Usuario(
                    nombre="Lucía Gómez (Ficticia)",
                    email="lucia.gomez.ficticia@example.com",
                    nro_socio="SOC-FICT-301",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_martin = Usuario(
                    nombre="Martín Pérez (Ficticio)",
                    email="martin.perez.ficticio@example.com",
                    nro_socio="SOC-FICT-302",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.PACIENTE,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                paciente_pendiente = Usuario(
                    nombre="Carla Ruiz (Ficticia)",
                    email="carla.ruiz.ficticia@example.com",
                    nro_socio="SOC-FICT-303",
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
                    nro_socio="ODO-FICT-301",
                    password_hash=hash_password("Pass1234!"),
                    rol=RolUsuario.ODONTOLOGO,
                    debe_cambiar_password=False,
                    perfil_completo=True,
                )
                odontologo_juan = Usuario(
                    nombre="Dr. Juan Pérez (Ficticio)",
                    email="juan.perez.ficticio@example.com",
                    nro_socio="ODO-FICT-302",
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

                # Seed Monday (0) template for Dra. Sofía Martín: 09:00-11:00, 30 min slots
                tpl_monday = PlantillaDisponibilidad(
                    odontologo_id=odontologo_sofia.id,
                    dia_semana=0,
                    hora_inicio=datetime.time(9, 0),
                    hora_fin=datetime.time(11, 0),
                    duracion_slot_minutos=30,
                    prestacion="Consulta general",
                )
                session.add(tpl_monday)
                await session.commit()

                return {
                    "paciente_lucia": paciente_lucia,
                    "paciente_martin": paciente_martin,
                    "paciente_pendiente": paciente_pendiente,
                    "recepcion": recepcion,
                    "odontologo_sofia": odontologo_sofia,
                    "odontologo_juan": odontologo_juan,
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


def _insert_turno(
    app,
    *,
    paciente_id: int,
    odontologo_id: int,
    inicio: datetime.datetime,
    fin: datetime.datetime,
    estado: EstadoTurno = EstadoTurno.SOLICITADO,
    motivo: str = "Consulta sintética",
) -> int:
    import anyio

    async def _create() -> int:
        async with app.state.session_factory() as session:
            turno = Turno(
                paciente_id=paciente_id,
                odontologo_id=odontologo_id,
                inicio=inicio,
                fin=fin,
                motivo=motivo,
                estado=estado,
                origen=OrigenTurno.ONLINE,
            )
            session.add(turno)
            await session.commit()
            await session.refresh(turno)
            return turno.id

    return anyio.run(_create)


def test_patch_turnos_happy_paths_and_slot_release_cb03(state_machine_client_and_context):
    """Task 3.1: Reception confirm/annul, patient cancel, dentist presente/ausente, and CB-03 slot release."""
    client, app, users, tokens = state_machine_client_and_context
    odontologo_id = users["odontologo_sofia"].id
    paciente_lucia_id = users["paciente_lucia"].id
    paciente_martin_id = users["paciente_martin"].id

    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_martin = {"Authorization": f"Bearer {tokens['paciente_martin']}"}
    h_recepcion = {"Authorization": f"Bearer {tokens['recepcion']}"}
    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}

    # Pick a Monday at least 7 days in the future so anticipation is well over 24h
    now_local = datetime.datetime.now(AR_TZ)
    future_monday = _next_weekday(now_local.date() + datetime.timedelta(days=3), 0)
    slot_0900_start = datetime.datetime.combine(future_monday, datetime.time(9, 0), tzinfo=AR_TZ)
    slot_0900_end = datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=AR_TZ)
    slot_0930_start = datetime.datetime.combine(future_monday, datetime.time(9, 30), tzinfo=AR_TZ)
    slot_0930_end = datetime.datetime.combine(future_monday, datetime.time(10, 0), tzinfo=AR_TZ)

    # 1. Patient Lucía books 09:00-09:30 via POST /api/turnos -> estado="solicitado"
    res_book = client.post(
        "/api/turnos",
        headers=h_lucia,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900_start.isoformat(),
            "fin": slot_0900_end.isoformat(),
            "motivo": "Control periódico sintético",
        },
    )
    assert res_book.status_code == 201
    turno_1_id = res_book.json()["id"]

    # 2. Reception confirms turno_1 (solicitado -> confirmado) -> 200 OK
    res_confirm = client.patch(
        f"/api/turnos/{turno_1_id}",
        headers=h_recepcion,
        json={"estado": "confirmado"},
    )
    assert res_confirm.status_code == 200
    assert res_confirm.json()["estado"] == "confirmado"

    # 3. Patient Lucía cancels her confirmed appointment with >24h notice (confirmado -> cancelado) -> 200 OK
    res_cancel = client.patch(
        f"/api/turnos/{turno_1_id}",
        headers=h_lucia,
        json={"estado": "cancelado"},
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["estado"] == "cancelado"

    # 4. CB-03: Slot 09:00-09:30 is immediately listed in GET /api/disponibilidad and bookable again via POST /api/turnos
    res_disp = client.get(
        "/api/disponibilidad",
        params={"odontologo_id": odontologo_id, "fecha": future_monday.isoformat()},
        headers=h_martin,
    )
    assert res_disp.status_code == 200
    free_starts = [
        datetime.datetime.fromisoformat(s["inicio"]) for s in res_disp.json()
    ]
    assert slot_0900_start in free_starts

    res_rebook = client.post(
        "/api/turnos",
        headers=h_martin,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900_start.isoformat(),
            "fin": slot_0900_end.isoformat(),
            "motivo": "Reserva tras cancelación sintética",
        },
    )
    assert res_rebook.status_code == 201
    turno_2_id = res_rebook.json()["id"]

    # 5. Reception annuls turno_2 (solicitado -> anulado) -> 200 OK and slot released again (CB-03)
    res_annul = client.patch(
        f"/api/turnos/{turno_2_id}",
        headers=h_recepcion,
        json={"estado": "anulado"},
    )
    assert res_annul.status_code == 200
    assert res_annul.json()["estado"] == "anulado"

    res_rebook_2 = client.post(
        "/api/turnos",
        headers=h_lucia,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0900_start.isoformat(),
            "fin": slot_0900_end.isoformat(),
            "motivo": "Reserva tras anulación sintética",
        },
    )
    assert res_rebook_2.status_code == 201
    turno_3_id = res_rebook_2.json()["id"]

    # 6. Reception confirms turno_3, then Dra. Sofía marks it "presente" -> 200 OK
    assert (
        client.patch(
            f"/api/turnos/{turno_3_id}",
            headers=h_recepcion,
            json={"estado": "confirmado"},
        ).status_code
        == 200
    )
    res_presente = client.patch(
        f"/api/turnos/{turno_3_id}",
        headers=h_sofia,
        json={"estado": "presente"},
    )
    assert res_presente.status_code == 200
    assert res_presente.json()["estado"] == "presente"

    # 7. Book 09:30-10:00, confirm it, and Dra. Sofía marks it "ausente" -> 200 OK
    res_book_4 = client.post(
        "/api/turnos",
        headers=h_martin,
        json={
            "odontologo_id": odontologo_id,
            "inicio": slot_0930_start.isoformat(),
            "fin": slot_0930_end.isoformat(),
            "motivo": "Consulta 09:30 sintética",
        },
    )
    assert res_book_4.status_code == 201
    turno_4_id = res_book_4.json()["id"]

    assert (
        client.patch(
            f"/api/turnos/{turno_4_id}",
            headers=h_recepcion,
            json={"estado": "confirmado"},
        ).status_code
        == 200
    )
    res_ausente = client.patch(
        f"/api/turnos/{turno_4_id}",
        headers=h_sofia,
        json={"estado": "ausente"},
    )
    assert res_ausente.status_code == 200
    assert res_ausente.json()["estado"] == "ausente"


def test_patch_turnos_rbac_bola_conflicts_anticipation_and_validation_errors(
    state_machine_client_and_context,
):
    """Task 3.1: Comprehensive error matrix (401, 403 role/BOLA/password, 404, 409 state conflict, 422 anticipation/schema)."""
    client, app, users, tokens = state_machine_client_and_context
    odontologo_sofia_id = users["odontologo_sofia"].id
    paciente_lucia_id = users["paciente_lucia"].id

    h_lucia = {"Authorization": f"Bearer {tokens['paciente_lucia']}"}
    h_martin = {"Authorization": f"Bearer {tokens['paciente_martin']}"}
    h_pendiente = {"Authorization": f"Bearer {tokens['paciente_pendiente']}"}
    h_recepcion = {"Authorization": f"Bearer {tokens['recepcion']}"}
    h_sofia = {"Authorization": f"Bearer {tokens['odontologo_sofia']}"}
    h_juan = {"Authorization": f"Bearer {tokens['odontologo_juan']}"}

    now_local = datetime.datetime.now(AR_TZ)
    inicio_48h = now_local + datetime.timedelta(hours=48)
    fin_48h = inicio_48h + datetime.timedelta(minutes=30)

    turno_solicitado_id = _insert_turno(
        app,
        paciente_id=paciente_lucia_id,
        odontologo_id=odontologo_sofia_id,
        inicio=inicio_48h,
        fin=fin_48h,
        estado=EstadoTurno.SOLICITADO,
    )
    turno_confirmado_id = _insert_turno(
        app,
        paciente_id=paciente_lucia_id,
        odontologo_id=odontologo_sofia_id,
        inicio=inicio_48h + datetime.timedelta(hours=1),
        fin=fin_48h + datetime.timedelta(hours=1),
        estado=EstadoTurno.CONFIRMADO,
    )

    # 1. 401 Unauthorized without token
    res_401 = client.patch(
        f"/api/turnos/{turno_solicitado_id}",
        json={"estado": "cancelado"},
    )
    assert res_401.status_code == 401

    # 2. 403 Forbidden when debe_cambiar_password=True
    res_pwd = client.patch(
        f"/api/turnos/{turno_solicitado_id}",
        headers=h_pendiente,
        json={"estado": "cancelado"},
    )
    assert res_pwd.status_code == 403
    assert res_pwd.json()["detail"] == "password_change_required"

    # 3. 404 Not Found on non-existent ID
    res_404 = client.patch(
        "/api/turnos/999999",
        headers=h_recepcion,
        json={"estado": "confirmado"},
    )
    assert res_404.status_code == 404

    # 4. 403 Forbidden: Role violations
    for bad_state in ("confirmado", "anulado", "presente", "ausente"):
        assert (
            client.patch(
                f"/api/turnos/{turno_solicitado_id}",
                headers=h_lucia,
                json={"estado": bad_state},
            ).status_code
            == 403
        )
    for bad_state in ("cancelado", "presente", "ausente"):
        assert (
            client.patch(
                f"/api/turnos/{turno_confirmado_id}",
                headers=h_recepcion,
                json={"estado": bad_state},
            ).status_code
            == 403
        )
    for bad_state in ("confirmado", "anulado", "cancelado"):
        assert (
            client.patch(
                f"/api/turnos/{turno_solicitado_id}",
                headers=h_sofia,
                json={"estado": bad_state},
            ).status_code
            == 403
        )

    # 5. 403 Forbidden (OWASP BOLA): Patient Martín attempting to cancel Lucía's appointment
    res_bola_patient = client.patch(
        f"/api/turnos/{turno_solicitado_id}",
        headers=h_martin,
        json={"estado": "cancelado"},
    )
    assert res_bola_patient.status_code == 403

    # 6. 403 Forbidden (OWASP BOLA): Dr. Juan attempting to mark Dra. Sofía's appointment presente/ausente
    for att_state in ("presente", "ausente"):
        res_bola_dentist = client.patch(
            f"/api/turnos/{turno_confirmado_id}",
            headers=h_juan,
            json={"estado": att_state},
        )
        assert res_bola_dentist.status_code == 403

    # 7. 409 Conflict: Invalid source state transitions
    # - Dentist Dra. Sofía attempting presente/ausente on unconfirmed 'solicitado' appointment
    for att_state in ("presente", "ausente"):
        res_409_unconfirmed = client.patch(
            f"/api/turnos/{turno_solicitado_id}",
            headers=h_sofia,
            json={"estado": att_state},
        )
        assert res_409_unconfirmed.status_code == 409

    # - Reception attempting to confirm an already 'confirmado' appointment
    res_409_already_conf = client.patch(
        f"/api/turnos/{turno_confirmado_id}",
        headers=h_recepcion,
        json={"estado": "confirmado"},
    )
    assert res_409_already_conf.status_code == 409

    # - Terminal state transitions (cancelado -> cancelado, anulado -> confirmado, presente -> cancelado)
    turno_presente_id = _insert_turno(
        app,
        paciente_id=paciente_lucia_id,
        odontologo_id=odontologo_sofia_id,
        inicio=inicio_48h + datetime.timedelta(hours=2),
        fin=fin_48h + datetime.timedelta(hours=2),
        estado=EstadoTurno.PRESENTE,
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_presente_id}",
            headers=h_lucia,
            json={"estado": "cancelado"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_presente_id}",
            headers=h_recepcion,
            json={"estado": "anulado"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_presente_id}",
            headers=h_sofia,
            json={"estado": "ausente"},
        ).status_code
        == 409
    )

    # 8. 422 Unprocessable Entity: Anticipation window < 24h (RN-TU-05)
    inicio_12h = now_local + datetime.timedelta(hours=12)
    fin_12h = inicio_12h + datetime.timedelta(minutes=30)
    turno_12h_id = _insert_turno(
        app,
        paciente_id=paciente_lucia_id,
        odontologo_id=odontologo_sofia_id,
        inicio=inicio_12h,
        fin=fin_12h,
        estado=EstadoTurno.CONFIRMADO,
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_12h_id}",
            headers=h_lucia,
            json={"estado": "cancelado"},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_12h_id}",
            headers=h_recepcion,
            json={"estado": "anulado"},
        ).status_code
        == 422
    )

    # 9. 422 Unprocessable Entity: Confirming a past appointment (RN-GL-02)
    inicio_past = now_local - datetime.timedelta(hours=2)
    fin_past = inicio_past + datetime.timedelta(minutes=30)
    turno_past_id = _insert_turno(
        app,
        paciente_id=paciente_lucia_id,
        odontologo_id=odontologo_sofia_id,
        inicio=inicio_past,
        fin=fin_past,
        estado=EstadoTurno.SOLICITADO,
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_past_id}",
            headers=h_recepcion,
            json={"estado": "confirmado"},
        ).status_code
        == 422
    )

    # 10. 422 Unprocessable Entity: Extra undeclared fields or invalid enum value (Hard Rule #1)
    assert (
        client.patch(
            f"/api/turnos/{turno_solicitado_id}",
            headers=h_lucia,
            json={"estado": "cancelado", "paciente_id": 999},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/turnos/{turno_solicitado_id}",
            headers=h_lucia,
            json={"estado": "inexistente"},
        ).status_code
        == 422
    )



