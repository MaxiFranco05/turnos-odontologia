import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.application.availability import SlotDisponible, calculate_free_slots
from app.domain.models.enums import RolUsuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.plantilla import SqlAlchemyPlantillaRepository
from app.infrastructure.repositories.turno import SqlAlchemyTurnoRepository
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository

router = APIRouter(prefix="/api/disponibilidad", tags=["disponibilidad"])


@router.get(
    "",
    response_model=list[SlotDisponible],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.PACIENTE,
                RolUsuario.RECEPCION,
                RolUsuario.ODONTOLOGO,
            )
        )
    ],
)
async def get_disponibilidad(
    request: Request,
    odontologo_id: int = Query(..., description="ID del odontólogo a consultar"),
    fecha: datetime.date = Query(..., description="Fecha a consultar (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> list[SlotDisponible]:
    """Computes available appointment slots for a dentist and date.
    
    Adheres strictly to:
    - Hard Rule #8: Noun-based REST URI (/api/disponibilidad).
    - Hard Rule #12: Returns only slot bounds and service (zero patient PII).
    - RN-AG-01 & RN-AG-02: Computed dynamically from templates minus active appointments.
    - RN-GL-01 & RN-AU-02: Authenticated and role-authorized.
    - RN-GL-02: Rejects past dates and filters elapsed slots for today.
    - CB-06: Verifies dentist exists and has RolUsuario.ODONTOLOGO.
    """
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    zone = ZoneInfo(settings.TIMEZONE)
    now_local = datetime.datetime.now(zone)

    # RN-GL-02: Rejection of past dates
    if fecha < now_local.date():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="RN-GL-02: No se puede consultar disponibilidad para fechas pasadas.",
        )

    # CB-06: Validation of dentist existence and role
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

    # Fetch templates for that weekday (0=Monday, 6=Sunday)
    plantilla_repo = SqlAlchemyPlantillaRepository(db)
    templates = await plantilla_repo.find_by_dentist_and_day(odontologo_id, fecha.weekday())

    # Fetch appointments for that day in clinic timezone
    start_of_day = datetime.datetime.combine(fecha, datetime.time.min, tzinfo=zone)
    end_of_day = datetime.datetime.combine(fecha, datetime.time.max, tzinfo=zone)
    turno_repo = SqlAlchemyTurnoRepository(db)
    turnos = await turno_repo.find_by_dentist_range(odontologo_id, start_of_day, end_of_day)

    try:
        free_slots = calculate_free_slots(
            fecha=fecha,
            templates=templates,
            turnos=turnos,
            timezone_str=settings.TIMEZONE,
            now_override=now_local,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return free_slots
