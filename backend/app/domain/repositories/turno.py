import datetime
from typing import Protocol
from app.domain.models.turno import Turno
from app.domain.repositories.base import BaseRepository


class TurnoRepository(BaseRepository[Turno, int], Protocol):
    """Domain repository interface for Turno entities."""

    async def get_by_id_for_update(self, id: int) -> Turno | None:
        """Retrieves an appointment by primary key acquiring a row-level FOR UPDATE lock."""
        ...

    async def find_by_dentist_range(
        self,
        odontologo_id: int,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Turno]:
        """Finds appointments for a dentist overlapping or within the time window."""
        ...

    async def find_by_patient_range(
        self,
        paciente_id: int,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Turno]:
        """Finds appointments for a patient within the time window."""
        ...

    async def find_overlapping(
        self,
        odontologo_id: int,
        inicio: datetime.datetime,
        fin: datetime.datetime,
        exclude_turno_id: int | None = None,
    ) -> list[Turno]:
        """Returns non-cancelled/non-annulled appointments for dentist overlapping [inicio, fin)."""
        ...

    async def find_overlapping_for_update(
        self,
        odontologo_id: int,
        inicio: datetime.datetime,
        fin: datetime.datetime,
        exclude_turno_id: int | None = None,
    ) -> list[Turno]:
        """Acquires row-level FOR UPDATE lock on active appointments overlapping [inicio, fin) (RN-AG-01)."""
        ...

    async def has_overlap(
        self,
        odontologo_id: int,
        inicio: datetime.datetime,
        fin: datetime.datetime,
        exclude_turno_id: int | None = None,
    ) -> bool:
        """Checks if any active appointment collides with the given interval (RN-AG-01)."""
        ...

    async def find_daily_agenda(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        odontologo_id: int | None = None,
    ) -> list[Turno]:
        """Finds all appointments within [start, end) eagerly loading patient and dentist, ordered by inicio, id."""
        ...
