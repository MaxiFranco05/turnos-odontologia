import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.domain.models.enums import RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.infrastructure.database import get_db
from app.infrastructure.repositories.plantilla import SqlAlchemyPlantillaRepository
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository

router = APIRouter(prefix="/api/plantillas", tags=["plantillas"])


class PlantillaCreate(BaseModel):
    """Schema for creating a weekly availability template.
    
    Hard Rule #1: extra='forbid' to reject undeclared attributes.
    """
    model_config = ConfigDict(extra="forbid")

    odontologo_id: int = Field(gt=0)
    dia_semana: int = Field(ge=0, le=6, description="0=Lunes, 6=Domingo")
    hora_inicio: datetime.time
    hora_fin: datetime.time
    duracion_slot_minutos: int = Field(gt=0, description="Duración en minutos, mayor a 0")
    prestacion: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _validate_time_range(self) -> "PlantillaCreate":
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser mayor que hora_inicio")
        return self


class PlantillaUpdate(BaseModel):
    """Schema for partially updating a weekly availability template (RFC 7396 JSON Merge Patch).
    
    Hard Rule #1: extra='forbid'.
    """
    model_config = ConfigDict(extra="forbid")

    dia_semana: int | None = Field(default=None, ge=0, le=6)
    hora_inicio: datetime.time | None = None
    hora_fin: datetime.time | None = None
    duracion_slot_minutos: int | None = Field(default=None, gt=0)
    prestacion: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def _validate_time_range(self) -> "PlantillaUpdate":
        if self.hora_inicio is not None and self.hora_fin is not None:
            if self.hora_fin <= self.hora_inicio:
                raise ValueError("hora_fin debe ser mayor que hora_inicio")
        return self


class PlantillaResponse(BaseModel):
    """Response schema for a weekly availability template."""
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    odontologo_id: int
    dia_semana: int
    hora_inicio: datetime.time
    hora_fin: datetime.time
    duracion_slot_minutos: int
    prestacion: str


async def _validate_dentist(odontologo_id: int, db: AsyncSession) -> None:
    """Validates that odontologo_id exists and has RolUsuario.ODONTOLOGO (CB-06)."""
    user_repo = SqlAlchemyUsuarioRepository(db)
    user = await user_repo.get_by_id(odontologo_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odontólogo con ID {odontologo_id} no encontrado.",
        )
    if user.rol != RolUsuario.ODONTOLOGO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario especificado no posee el rol de odontólogo.",
        )


@router.post(
    "",
    response_model=PlantillaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RolUsuario.RECEPCION))],
)
async def create_plantilla(
    payload: PlantillaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlantillaResponse:
    """Creates a new weekly availability template for a dentist.
    
    Restricted to Reception role (RN-GL-01, RN-AU-02).
    Enforces non-overlap invariant RN-AG-01 and dentist validation CB-06.
    """
    await _validate_dentist(payload.odontologo_id, db)

    repo = SqlAlchemyPlantillaRepository(db)
    overlaps = await repo.find_overlapping_templates(
        odontologo_id=payload.odontologo_id,
        dia_semana=payload.dia_semana,
        hora_inicio=payload.hora_inicio,
        hora_fin=payload.hora_fin,
    )
    if overlaps:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RN-AG-01: Existe una plantilla horaria superpuesta para el odontólogo y día especificados.",
        )

    plantilla = PlantillaDisponibilidad(
        odontologo_id=payload.odontologo_id,
        dia_semana=payload.dia_semana,
        hora_inicio=payload.hora_inicio,
        hora_fin=payload.hora_fin,
        duracion_slot_minutos=payload.duracion_slot_minutos,
        prestacion=payload.prestacion,
    )
    created = await repo.add(plantilla)
    await db.commit()
    await db.refresh(created)
    return PlantillaResponse.model_validate(created)


@router.get(
    "",
    response_model=list[PlantillaResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(RolUsuario.RECEPCION))],
)
async def list_plantillas(
    db: Annotated[AsyncSession, Depends(get_db)],
    odontologo_id: int | None = Query(default=None),
) -> list[PlantillaResponse]:
    """Lists weekly availability templates, optionally filtered by dentist ID."""
    repo = SqlAlchemyPlantillaRepository(db)
    if odontologo_id is not None:
        plantillas = await repo.find_by_dentist(odontologo_id)
    else:
        stmt = select(PlantillaDisponibilidad).order_by(
            PlantillaDisponibilidad.dia_semana,
            PlantillaDisponibilidad.hora_inicio,
        )
        result = await db.scalars(stmt)
        plantillas = list(result.all())

    return [PlantillaResponse.model_validate(p) for p in plantillas]


@router.patch(
    "/{id}",
    response_model=PlantillaResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(RolUsuario.RECEPCION))],
)
async def update_plantilla(
    id: int,
    payload: PlantillaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlantillaResponse:
    """Partially updates an existing template (Hard Rule #9: PATCH instead of PUT).
    
    Empty body {} is treated as an idempotent no-op returning 200 OK (RFC 7396).
    Enforces merged state time ordering and overlap detection excluding self.
    """
    repo = SqlAlchemyPlantillaRepository(db)
    plantilla = await repo.get_by_id(id)
    if plantilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plantilla con ID {id} no encontrada.",
        )

    patch_data = payload.model_dump(exclude_unset=True)
    if not patch_data:
        return PlantillaResponse.model_validate(plantilla)

    effective_dia = patch_data.get("dia_semana", plantilla.dia_semana)
    effective_inicio = patch_data.get("hora_inicio", plantilla.hora_inicio)
    effective_fin = patch_data.get("hora_fin", plantilla.hora_fin)
    effective_duracion = patch_data.get("duracion_slot_minutos", plantilla.duracion_slot_minutos)
    effective_prestacion = patch_data.get("prestacion", plantilla.prestacion)

    if effective_fin <= effective_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="hora_fin debe ser mayor que hora_inicio en el estado resultante.",
        )

    overlaps = await repo.find_overlapping_templates(
        odontologo_id=plantilla.odontologo_id,
        dia_semana=effective_dia,
        hora_inicio=effective_inicio,
        hora_fin=effective_fin,
        exclude_id=plantilla.id,
    )
    if overlaps:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RN-AG-01: La actualización solicitada superpone la plantilla con otra existente.",
        )

    plantilla.dia_semana = effective_dia
    plantilla.hora_inicio = effective_inicio
    plantilla.hora_fin = effective_fin
    plantilla.duracion_slot_minutos = effective_duracion
    plantilla.prestacion = effective_prestacion

    await db.commit()
    await db.refresh(plantilla)
    return PlantillaResponse.model_validate(plantilla)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RolUsuario.RECEPCION))],
)
async def delete_plantilla(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Deletes an availability template by ID."""
    repo = SqlAlchemyPlantillaRepository(db)
    plantilla = await repo.get_by_id(id)
    if plantilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plantilla con ID {id} no encontrada.",
        )

    await repo.delete(plantilla)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
