from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
IDT = TypeVar("IDT")


class SqlAlchemyBaseRepository(Generic[ModelT, IDT]):
    """Generic async SQLAlchemy 2.0 repository implementation using select()."""

    def __init__(self, session: AsyncSession, model_cls: type[ModelT]) -> None:
        self._session = session
        self._model_cls = model_cls

    async def get_by_id(self, id: IDT) -> ModelT | None:
        """Retrieves entity by ID using modern 2.0 session.get()."""
        return await self._session.get(self._model_cls, id)

    async def list_all(self) -> list[ModelT]:
        """Lists all records using SQLAlchemy 2.0 select()."""
        stmt = select(self._model_cls)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def add(self, entity: ModelT) -> ModelT:
        """Adds entity to the session and flushes pending changes."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Deletes entity from session and flushes."""
        await self._session.delete(entity)
        await self._session.flush()
