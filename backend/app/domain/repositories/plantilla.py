from typing import Protocol
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.repositories.base import BaseRepository


class PlantillaRepository(BaseRepository[PlantillaDisponibilidad, int], Protocol):
    """Domain repository interface for PlantillaDisponibilidad entities."""

    async def find_by_dentist(self, odontologo_id: int) -> list[PlantillaDisponibilidad]:
        """Finds all availability templates configured for a dentist."""
        ...

    async def find_by_dentist_and_day(
        self,
        odontologo_id: int,
        dia_semana: int,
    ) -> list[PlantillaDisponibilidad]:
        """Finds templates for a dentist on a specific day of the week (0=Monday, 6=Sunday)."""
        ...
