from typing import Generic, Protocol, TypeVar

ModelT = TypeVar("ModelT")
IDT = TypeVar("IDT")


class BaseRepository(Protocol[ModelT, IDT]):
    """Generic repository protocol defining standard CRUD operations."""

    async def get_by_id(self, id: IDT) -> ModelT | None:
        """Retrieves an entity by its primary key identifier."""
        ...

    async def list_all(self) -> list[ModelT]:
        """Lists all persisted entities of this type."""
        ...

    async def add(self, entity: ModelT) -> ModelT:
        """Adds a new entity or merges it into the persistent store."""
        ...

    async def delete(self, entity: ModelT) -> None:
        """Removes an entity from the persistent store."""
        ...
