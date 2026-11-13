import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.application.turnos import (
    get_clinic_date_range_bounds,
    get_clinic_day_bounds,
    get_clinic_month_bounds,
    summarize_dentist_month_appointments,
)
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository

router = APIRouter(prefix="/api/mis-turnos", tags=["mis-turnos"])


class PacienteResumenResponse(BaseModel):
    """Least-privilege patient summary embedded in dentist agenda items.

    Hard Rule #1: extra='forbid'.
    OWASP API3:2023 (BOPLA): projects only identification fields and never exposes
    password_hash, debe_cambiar_password, or rol.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    nro_socio: str | None
    email: str | None


class OdontologoResumenResponse(BaseModel):
    """Least-privilege dentist summary embedded in patient portal appointment items.

    Hard Rule #1: extra='forbid'.
    OWASP API3:2023 (BOPLA): projects only identification fields and never exposes
    password_hash, debe_cambiar_password, or rol.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    nro_socio: str | None
    email: str | None


class MisTurnosOdontologoItemResponse(BaseModel):
    """Response item for a dentist's daily self-agenda query (GET /api/mis-turnos?fecha=YYYY-MM-DD)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    paciente_id: int
    odontologo_id: int
    inicio: datetime.datetime
    fin: datetime.datetime
    motivo: str
    estado: EstadoTurno
    origen: OrigenTurno
    paciente: PacienteResumenResponse


class MisTurnosPacienteItemResponse(BaseModel):
    """Response item for a patient's self-appointment query (GET /api/mis-turnos?fecha_desde=&fecha_hasta=)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    paciente_id: int
    odontologo_id: int
    inicio: datetime.datetime
    fin: datetime.datetime
    motivo: str
    estado: EstadoTurno
    origen: OrigenTurno
    odontologo: OdontologoResumenResponse


@router.get(
    "",
    response_model=list[MisTurnosOdontologoItemResponse] | list[MisTurnosPacienteItemResponse],
    status_code=status.HTTP_200_OK,
)
async def list_mis_turnos(
    request: Request,
    current_user: Annotated[
        Usuario,
        Depends(require_roles(RolUsuario.ODONTOLOGO, RolUsuario.PACIENTE)),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    fecha: Annotated[
        datetime.date | None,
        Query(description="Fecha de la agenda en formato YYYY-MM-DD (exclusivo odontólogo)"),
    ] = None,
    fecha_desde: Annotated[
        datetime.date | None,
        Query(description="Fecha inicial inclusiva en formato YYYY-MM-DD (exclusivo paciente)"),
    ] = None,
    fecha_hasta: Annotated[
        datetime.date | None,
        Query(description="Fecha final inclusiva en formato YYYY-MM-DD (exclusivo paciente)"),
    ] = None,
) -> list[MisTurnosOdontologoItemResponse] | list[MisTurnosPacienteItemResponse]:
    """Returns self-appointments scoped to the authenticated user's role and identity.

    Strictly adheres to:
    - Hard Rule #1: Strict Pydantic response schemas with extra='forbid' (OWASP BOPLA).
    - Hard Rule #2: SQLAlchemy 2.0 select() with selectinload via SqlAlchemyTurnoRepository.
    - Hard Rule #3: Pure synchronous get_clinic_day_bounds / get_clinic_date_range_bounds helpers.
    - Hard Rule #8: Noun-based URI (/api/mis-turnos).
    - RN-AU-02, RN-GL-01, US-004 & US-007: Binds odontologo_id or paciente_id = current_user.id from JWT token (OWASP BOLA).
    """
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    turno_repo = SqlAlchemyTurnoRepository(db)

    if current_user.rol == RolUsuario.ODONTOLOGO:
        if fecha is None or fecha_desde is not None or fecha_hasta is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El rol odontólogo requiere el parámetro 'fecha' y no admite 'fecha_desde' ni 'fecha_hasta'.",
            )
        day_start, day_end = get_clinic_day_bounds(
            fecha=fecha,
            timezone_str=settings.TIMEZONE,
        )
        turnos = await turno_repo.find_by_dentist_range(
            odontologo_id=current_user.id,
            start=day_start,
            end=day_end,
        )
        return [MisTurnosOdontologoItemResponse.model_validate(t) for t in turnos]

    # RolUsuario.PACIENTE branch
    if fecha is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El parámetro 'fecha' es exclusivo de la vista de odontólogo; utilice 'fecha_desde' y/o 'fecha_hasta'.",
        )

    try:
        range_start, range_end = get_clinic_date_range_bounds(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            timezone_str=settings.TIMEZONE,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    turnos = await turno_repo.find_by_patient_range(
        paciente_id=current_user.id,
        start=range_start,
        end=range_end,
    )
    return [MisTurnosPacienteItemResponse.model_validate(t) for t in turnos]


class CalendarioDiaResumenResponse(BaseModel):
    """Daily appointment summary counts for a dentist's monthly calendar."""

    model_config = ConfigDict(extra="forbid")

    fecha: datetime.date
    confirmados: int
    solicitados: int
    atendidos: int
    total_activos: int


class CalendarioMesResponse(BaseModel):
    """Monthly calendar summary response for the authenticated dentist."""

    model_config = ConfigDict(extra="forbid")

    anio: int
    mes: int
    dias: list[CalendarioDiaResumenResponse]


@router.get("/calendario", response_model=CalendarioMesResponse)
async def get_mis_turnos_calendario(
    request: Request,
    current_user: Annotated[Usuario, Depends(require_roles(RolUsuario.ODONTOLOGO))],
    db: Annotated[AsyncSession, Depends(get_db)],
    anio: int | None = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
) -> CalendarioMesResponse:
    """Return active appointment counts per day for the authenticated dentist's month."""
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    today_clinic = datetime.datetime.now(ZoneInfo(settings.TIMEZONE)).date()
    target_year = anio if anio is not None else today_clinic.year
    target_month = mes if mes is not None else today_clinic.month

    month_start, month_end = get_clinic_month_bounds(
        anio=target_year,
        mes=target_month,
        timezone_str=settings.TIMEZONE,
    )

    turno_repo = SqlAlchemyTurnoRepository(db)
    turnos = await turno_repo.find_by_dentist_range(
        odontologo_id=current_user.id,
        start=month_start,
        end=month_end,
    )
    summary_items = summarize_dentist_month_appointments(
        turnos=turnos,
        anio=target_year,
        mes=target_month,
        timezone_str=settings.TIMEZONE,
    )
    return CalendarioMesResponse(
        anio=target_year,
        mes=target_month,
        dias=[CalendarioDiaResumenResponse(**item) for item in summary_items],
    )

