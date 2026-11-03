import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.application.turnos import (
    DEFAULT_CLINIC_TIMEZONE,
    AnticipationWindowError,
    InvalidStateTransitionError,
    UnauthorizedTransitionError,
    validate_slot_matches_template,
    validate_state_transition,
)
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.plantilla import SqlAlchemyPlantillaRepository
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository

router = APIRouter(prefix="/api/turnos", tags=["turnos"])


class TurnoCreate(BaseModel):
    """Schema for patient-initiated online appointment requests (POST /api/turnos).

    Hard Rule #1: extra='forbid' and str_strip_whitespace=True.
    OWASP API1/API3: omits paciente_id, estado, and origen to prevent BOLA and mass assignment.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    odontologo_id: int = Field(gt=0, description="ID del odontólogo a reservar")
    inicio: datetime.datetime
    fin: datetime.datetime
    motivo: str = Field(min_length=1, max_length=255, description="Motivo de consulta")

    @model_validator(mode="after")
    def _validate_chronological_order(self) -> "TurnoCreate":
        zone = ZoneInfo(DEFAULT_CLINIC_TIMEZONE)
        inicio_cmp = (
            self.inicio.replace(tzinfo=zone)
            if self.inicio.tzinfo is None or self.inicio.tzinfo.utcoffset(self.inicio) is None
            else self.inicio.astimezone(zone)
        )
        fin_cmp = (
            self.fin.replace(tzinfo=zone)
            if self.fin.tzinfo is None or self.fin.tzinfo.utcoffset(self.fin) is None
            else self.fin.astimezone(zone)
        )
        if fin_cmp <= inicio_cmp:
            raise ValueError("fin debe ser estrictamente mayor que inicio")
        return self


class TurnoResponse(BaseModel):
    """Response schema for a created appointment request."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    paciente_id: int
    odontologo_id: int
    inicio: datetime.datetime
    fin: datetime.datetime
    motivo: str
    estado: EstadoTurno
    origen: OrigenTurno
    creado_en: datetime.datetime
    actualizado_en: datetime.datetime


class TurnoEstadoUpdate(BaseModel):
    """Schema for partial appointment state transitions (PATCH /api/turnos/{id}).

    Hard Rule #1: extra='forbid' to reject undeclared fields and prevent mass assignment.
    Hard Rules #8 & #9: resource-oriented PATCH replacing verb subpaths.
    """

    model_config = ConfigDict(extra="forbid")

    estado: EstadoTurno


@router.post(
    "",
    response_model=TurnoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_turno_request(
    request: Request,
    payload: TurnoCreate,
    current_user: Annotated[Usuario, Depends(require_roles(RolUsuario.PACIENTE))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TurnoResponse:
    """Creates an online appointment request in state 'solicitado' for the authenticated patient.

    Strictly adheres to:
    - Hard Rule #1: Strict Pydantic validation with extra='forbid'.
    - Hard Rule #2: SQLAlchemy 2.0 select() with FOR UPDATE row locking.
    - Hard Rule #3: Pure synchronous template/timezone slot validator.
    - Hard Rule #8: Noun-based URI (/api/turnos).
    - Hard Rule #13 & RN-AG-01: Server-side transactional anti-overlap enforcement.
    - RN-TU-01 & RN-GL-01: Restricted to RolUsuario.PACIENTE, binding paciente_id = current_user.id.
    - RN-AG-02 & CB-02: Validates exact alignment with PlantillaDisponibilidad slot.
    - RN-GL-02 & CB-05: Rejects past dates and already elapsed same-day slots in TIMEZONE.
    - CB-06: Verifies odontologo_id exists (404) and has RolUsuario.ODONTOLOGO (422).
    """
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    zone = ZoneInfo(settings.TIMEZONE)
    now_local = datetime.datetime.now(zone)

    # CB-06 + Concurrency serialization: Lock parent dentist row (SELECT ... FOR UPDATE)
    # to serialize concurrent empty-slot bookings for the same professional in PostgreSQL.
    dentist_stmt = (
        select(Usuario)
        .where(Usuario.id == payload.odontologo_id)
        .with_for_update()
    )
    dentist = await db.scalar(dentist_stmt)
    if dentist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con ID {payload.odontologo_id} no encontrado.",
        )
    if dentist.rol != RolUsuario.ODONTOLOGO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario especificado no posee el rol de odontólogo.",
        )

    # Normalize start date in clinic timezone to load weekday templates
    inicio_in_zone = (
        payload.inicio.replace(tzinfo=zone)
        if payload.inicio.tzinfo is None or payload.inicio.tzinfo.utcoffset(payload.inicio) is None
        else payload.inicio.astimezone(zone)
    )
    plantilla_repo = SqlAlchemyPlantillaRepository(db)
    templates = await plantilla_repo.find_by_dentist_and_day(
        payload.odontologo_id,
        inicio_in_zone.date().weekday(),
    )

    try:
        inicio_local, fin_local = validate_slot_matches_template(
            inicio=payload.inicio,
            fin=payload.fin,
            templates=templates,
            timezone_str=settings.TIMEZONE,
            now_override=now_local,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # RN-AG-01 & Hard Rule #13: Transactional overlap check with SELECT ... FOR UPDATE
    turno_repo = SqlAlchemyTurnoRepository(db)
    overlaps = await turno_repo.find_overlapping_for_update(
        odontologo_id=payload.odontologo_id,
        inicio=inicio_local,
        fin=fin_local,
    )
    if overlaps:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RN-AG-01: El horario solicitado ya se encuentra ocupado para el odontólogo seleccionado.",
        )

    nuevo_turno = Turno(
        paciente_id=current_user.id,
        odontologo_id=payload.odontologo_id,
        inicio=inicio_local,
        fin=fin_local,
        motivo=payload.motivo,
        estado=EstadoTurno.SOLICITADO,
        origen=OrigenTurno.ONLINE,
    )

    try:
        created = await turno_repo.add(nuevo_turno)
        await db.commit()
        await db.refresh(created)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RN-AG-01: Conflicto concurrente al reservar el turno; el horario ya fue ocupado.",
        ) from exc

    return TurnoResponse.model_validate(created)


@router.patch(
    "/{id}",
    response_model=TurnoResponse,
    status_code=status.HTTP_200_OK,
)
async def transition_turno_state(
    id: int,
    request: Request,
    payload: TurnoEstadoUpdate,
    current_user: Annotated[
        Usuario,
        Depends(
            require_roles(
                RolUsuario.PACIENTE,
                RolUsuario.RECEPCION,
                RolUsuario.ODONTOLOGO,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TurnoResponse:
    """Transitions the lifecycle state of an existing appointment (PATCH /api/turnos/{id}).

    Strictly adheres to:
    - Hard Rule #1: TurnoEstadoUpdate with ConfigDict(extra='forbid').
    - Hard Rule #2: SQLAlchemy 2.0 select(Turno).where(Turno.id == id).with_for_update().
    - Hard Rule #3: Pure synchronous validate_state_transition(...) in application layer.
    - Hard Rules #8 & #9: Resource-oriented PATCH URI without verbs in path.
    - RN-TU-01..05, RN-GL-01..02, RN-AU-02: Role allowlist, BOLA ownership check, state matrix, and 24h anticipation.
    """
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    zone = ZoneInfo(settings.TIMEZONE)
    now_local = datetime.datetime.now(zone)

    turno_repo = SqlAlchemyTurnoRepository(db)
    turno = await turno_repo.get_by_id_for_update(id)
    if turno is None:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turno con ID {id} no encontrado.",
        )

    try:
        validate_state_transition(
            actor_rol=current_user.rol,
            actor_user_id=current_user.id,
            turno_paciente_id=turno.paciente_id,
            turno_odontologo_id=turno.odontologo_id,
            estado_actual=turno.estado,
            nuevo_estado=payload.estado,
            turno_inicio=turno.inicio,
            now_local=now_local,
            cancel_min_hours=settings.CANCEL_MIN_HOURS,
            timezone_str=settings.TIMEZONE,
        )
    except UnauthorizedTransitionError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidStateTransitionError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AnticipationWindowError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    turno.estado = payload.estado
    await db.commit()
    await db.refresh(turno)
    return TurnoResponse.model_validate(turno)

