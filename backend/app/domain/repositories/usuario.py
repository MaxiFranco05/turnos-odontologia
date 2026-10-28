from typing import Protocol
from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.domain.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario, int], Protocol):
    """Domain repository interface for Usuario entities."""

    async def get_by_email(self, email: str) -> Usuario | None:
        """Finds user by exact email address."""
        ...

    async def get_by_nro_socio(self, nro_socio: str) -> Usuario | None:
        """Finds user by affiliate/socio number."""
        ...

    async def get_by_identifier(self, identifier: str) -> Usuario | None:
        """Finds user by either email or socio number (RN-AU-01)."""
        ...

    async def list_by_rol(self, rol: RolUsuario) -> list[Usuario]:
        """Lists users having a specific system role."""
        ...
