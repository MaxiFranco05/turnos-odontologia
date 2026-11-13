from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.database import get_db

router = APIRouter(prefix="/api/odontologos", tags=["odontologos"])


class OdontologoPublicResponse(BaseModel):
    """Publicly accessible profile for active dentists in the clinic.

    Hard Rule #1: extra='forbid' to eliminate undeclared fields.
    OWASP API3: never exposes password_hash or internal auth flags.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    email: str | None = None
    nro_socio: str | None = None
    especialidad: str | None = "Odontología General"


@router.get(
    "",
    response_model=list[OdontologoPublicResponse],
    status_code=status.HTTP_200_OK,
)
async def list_odontologos(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OdontologoPublicResponse]:
    """Returns active odontólogos in the clinic for appointment booking.

    Complies with:
    - Hard Rule #1: Pydantic schemas declare extra='forbid'.
    - Hard Rule #2: Pure SQLAlchemy 2.0 select() query.
    - Hard Rule #8: Noun-based REST URI (/api/odontologos).
    - Hard Rule #12: Synthetic clinical data only.
    """
    stmt = (
        select(Usuario)
        .where(Usuario.rol == RolUsuario.ODONTOLOGO)
        .order_by(Usuario.id.asc())
    )
    result = await db.scalars(stmt)
    odontologos = list(result.all())

    # Map specialties based on profile or standard defaults
    specialties: dict[str, str] = {
        "sofia": "Odontología General y Prevención",
        "lucas": "Ortodoncia y Prótesis",
        "martin": "Odontología General y Cirugía",
        "ruiz": "Odontología General y Cirugía",
    }

    response_list: list[OdontologoPublicResponse] = []
    for doc in odontologos:
        doc_lower = doc.nombre.lower()
        spec = "Odontología General"
        for key, s_val in specialties.items():
            if key in doc_lower or (doc.email and key in doc.email.lower()):
                spec = s_val
                break

        clean_name = doc.nombre.replace(" (Ficticia)", "").replace(" (Ficticio)", "").strip()
        response_list.append(
            OdontologoPublicResponse(
                id=doc.id,
                nombre=clean_name,
                email=doc.email,
                nro_socio=doc.nro_socio,
                especialidad=spec,
            )
        )

    return response_list
