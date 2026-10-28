from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.repositories.plantilla import PlantillaRepository
from app.infrastructure.repositories.base import SqlAlchemyBaseRepository


class SqlAlchemyPlantillaRepository(
    SqlAlchemyBaseRepository[PlantillaDisponibilidad, int],
    PlantillaRepository,
):
    """Async SQLAlchemy 2.0 repository for PlantillaDisponibilidad entities using select()."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=PlantillaDisponibilidad)

    async def find_by_dentist(self, odontologo_id: int) -> list[PlantillaDisponibilidad]:
        """Finds all availability templates configured for a dentist."""
        stmt = (
            select(PlantillaDisponibilidad)
            .where(PlantillaDisponibilidad.odontologo_id == odontologo_id)
            .order_by(PlantillaDisponibilidad.dia_semana, PlantillaDisponibilidad.hora_inicio)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def find_by_dentist_and_day(
        self,
        odontologo_id: int,
        dia_semana: int,
    ) -> list[PlantillaDisponibilidad]:
        """Finds templates for a dentist on a specific day of the week."""
        stmt = (
            select(PlantillaDisponibilidad)
            .where(
                PlantillaDisponibilidad.odontologo_id == odontologo_id,
                PlantillaDisponibilidad.dia_semana == dia_semana,
            )
            .order_by(PlantillaDisponibilidad.hora_inicio)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())
