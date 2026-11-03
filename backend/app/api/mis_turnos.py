import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.application.turnos import get_clinic_day_bounds
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


@router.get(
    "",
    response_model=list[MisTurnosOdontologoItemResponse],
    status_code=status.HTTP_200_OK,
)
async def list_mis_turnos(
    request: Request,
    fecha: Annotated[datetime.date, Query(description="Fecha de la agenda en formato YYYY-MM-DD")],
    current_user: Annotated[Usuario, Depends(require_roles(RolUsuario.ODONTOLOGO))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MisTurnosOdontologoItemResponse]:
    """Returns the authenticated dentist's appointments for the given clinic date.

    Strictly adheres to:
    - Hard Rule #1: Strict Pydantic response schemas with extra='forbid'.
    - Hard Rule #2: SQLAlchemy 2.0 select() via SqlAlchemyTurnoRepository.find_by_dentist_range.
    - Hard Rule #3: Pure synchronous get_clinic_day_bounds(...) helper.
    - Hard Rule #8: Noun-based URI (/api/mis-turnos).
    - RN-AU-02, RN-GL-01 & US-007 CA-1: Binds odontologo_id = current_user.id from JWT token.
    """
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    day_start, day_end = get_clinic_day_bounds(
        fecha=fecha,
        timezone_str=settings.TIMEZONE,
    )

    turno_repo = SqlAlchemyTurnoRepository(db)
    turnos = await turno_repo.find_by_dentist_range(
        odontologo_id=current_user.id,
        start=day_start,
        end=day_end,
    )

    return [MisTurnosOdontologoItemResponse.model_validate(t) for t in turnos]
