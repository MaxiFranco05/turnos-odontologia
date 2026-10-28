import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import EstadoTurno
from app.domain.models.turno import Turno
from app.domain.repositories.turno import TurnoRepository
from app.infrastructure.repositories.base import SqlAlchemyBaseRepository


class SqlAlchemyTurnoRepository(SqlAlchemyBaseRepository[Turno, int], TurnoRepository):
    """Async SQLAlchemy 2.0 repository for Turno entities using select()."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=Turno)

    async def find_by_dentist_range(
        self,
        odontologo_id: int,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Turno]:
        """Finds appointments for a dentist overlapping or within the time window."""
        stmt = (
            select(Turno)
            .where(
                Turno.odontologo_id == odontologo_id,
                Turno.inicio < end,
                Turno.fin > start,
            )
            .order_by(Turno.inicio)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def find_by_patient_range(
        self,
        paciente_id: int,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Turno]:
        """Finds appointments for a patient within the time window."""
        stmt = (
            select(Turno)
            .where(
                Turno.paciente_id == paciente_id,
                Turno.inicio < end,
                Turno.fin > start,
            )
            .order_by(Turno.inicio)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def find_overlapping(
        self,
        odontologo_id: int,
        inicio: datetime.datetime,
        fin: datetime.datetime,
        exclude_turno_id: int | None = None,
    ) -> list[Turno]:
        """Returns active non-cancelled/non-annulled appointments colliding with [inicio, fin)."""
        stmt = select(Turno).where(
            Turno.odontologo_id == odontologo_id,
            Turno.estado.not_in([EstadoTurno.CANCELADO, EstadoTurno.ANULADO]),
            Turno.inicio < fin,
            Turno.fin > inicio,
        )
        if exclude_turno_id is not None:
            stmt = stmt.where(Turno.id != exclude_turno_id)

        result = await self._session.scalars(stmt)
        return list(result.all())

    async def has_overlap(
        self,
        odontologo_id: int,
        inicio: datetime.datetime,
        fin: datetime.datetime,
        exclude_turno_id: int | None = None,
    ) -> bool:
        """Checks if an active appointment collides with the time slot (RN-AG-01)."""
        overlaps = await self.find_overlapping(
            odontologo_id=odontologo_id,
            inicio=inicio,
            fin=fin,
            exclude_turno_id=exclude_turno_id,
        )
        return len(overlaps) > 0
