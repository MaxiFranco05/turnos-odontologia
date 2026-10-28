from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.domain.repositories.usuario import UsuarioRepository
from app.infrastructure.repositories.base import SqlAlchemyBaseRepository


class SqlAlchemyUsuarioRepository(SqlAlchemyBaseRepository[Usuario, int], UsuarioRepository):
    """Async SQLAlchemy 2.0 repository for Usuario entities using select()."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model_cls=Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        """Finds user by exact email using select()."""
        stmt = select(Usuario).where(Usuario.email == email)
        result = await self._session.scalars(stmt)
        return result.first()

    async def get_by_nro_socio(self, nro_socio: str) -> Usuario | None:
        """Finds user by affiliate/socio number using select()."""
        stmt = select(Usuario).where(Usuario.nro_socio == nro_socio)
        result = await self._session.scalars(stmt)
        return result.first()

    async def get_by_identifier(self, identifier: str) -> Usuario | None:
        """Finds user by either email or socio number using select() and or_()."""
        stmt = select(Usuario).where(
            or_(
                Usuario.email == identifier,
                Usuario.nro_socio == identifier,
            )
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def list_by_rol(self, rol: RolUsuario) -> list[Usuario]:
        """Lists users having a specific role using select()."""
        stmt = select(Usuario).where(Usuario.rol == rol)
        result = await self._session.scalars(stmt)
        return list(result.all())
