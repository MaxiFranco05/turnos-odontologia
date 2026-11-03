import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.application.turnos import get_clinic_day_bounds
from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository

router = APIRouter(prefix="/api/agenda", tags=["agenda"])


class AgendaPacienteResponse(BaseModel):
    """Safe patient contact projection for reception agenda view (OWASP BOPLA, Hard Rule #1)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    nro_socio: str | None
    email: str | None


class AgendaOdontologoResponse(BaseModel):
    """Safe dentist contact projection for reception agenda view (OWASP BOPLA, Hard Rule #1)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    email: str | None


class AgendaTurnoDiaResponse(BaseModel):
    """Response item for daily reception agenda (GET /api/agenda/dia?fecha=YYYY-MM-DD[&odontologo_id=N])."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    paciente_id: int
    odontologo_id: int
    inicio: datetime.datetime
    fin: datetime.datetime
    motivo: str
    estado: EstadoTurno
    origen: OrigenTurno
    paciente: AgendaPacienteResponse
    odontologo: AgendaOdontologoResponse


@router.get(
    "/dia",
    response_model=list[AgendaTurnoDiaResponse],
    status_code=status.HTTP_200_OK,
)
async def get_agenda_dia(
    request: Request,
    fecha: Annotated[datetime.date, Query(description="Fecha de la agenda en formato YYYY-MM-DD")],
    current_user: Annotated[Usuario, Depends(require_roles(RolUsuario.RECEPCION))],
    db: Annotated[AsyncSession, Depends(get_db)],
    odontologo_id: Annotated[int | None, Query(description="Filtrar por ID de odontólogo")] = None,
) -> list[AgendaTurnoDiaResponse]:
    """Returns all clinic appointments for a calendar date, with optional dentist filter.

    Strictly complies with:
    - RN-GL-01 & RN-AU-02: Restricted exclusively to Reception role (403 for other roles).
    - Hard Rule #1: Pydantic schemas declare extra='forbid' to eliminate BOPLA.
    - Hard Rule #2: Uses SQLAlchemy 2.0 select() with selectinload for paciente and odontologo.
    - Hard Rule #3: Pure synchronous get_clinic_day_bounds helper.
    - Hard Rule #8: Noun-based REST URI (/api/agenda/dia).
    - CB-06: Validates dentist existence (404) and role (422).
    - US-005 CA-1/CA-2: Preserves patient cancellations and online booking origins.
    """
    if odontologo_id is not None:
        user_repo = SqlAlchemyUsuarioRepository(db)
        dentist = await user_repo.get_by_id(odontologo_id)
        if dentist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Odontólogo con ID {odontologo_id} no encontrado.",
            )
        if dentist.rol != RolUsuario.ODONTOLOGO:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El usuario especificado no posee el rol de odontólogo.",
            )

    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    day_start, day_end = get_clinic_day_bounds(
        fecha=fecha,
        timezone_str=settings.TIMEZONE,
    )

    turno_repo = SqlAlchemyTurnoRepository(db)
    turnos = await turno_repo.find_daily_agenda(
        start=day_start,
        end=day_end,
        odontologo_id=odontologo_id,
    )

    return [AgendaTurnoDiaResponse.model_validate(t) for t in turnos]
