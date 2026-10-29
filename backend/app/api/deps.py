from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository
from app.infrastructure.security import decode_access_token

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    """Validates Bearer JWT, loads Usuario from DB, and attaches it to request.state.user."""
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de autenticación inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized_exc

    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()

    try:
        payload = decode_access_token(credentials.credentials, settings)
        sub = payload.get("sub")
        if sub is None:
            raise unauthorized_exc
        user_id = int(str(sub))
    except (JWTError, ValueError, TypeError) as exc:
        raise unauthorized_exc from exc

    repo = SqlAlchemyUsuarioRepository(db)
    usuario = await repo.get_by_id(user_id)
    if usuario is None:
        raise unauthorized_exc

    request.state.user = usuario
    return usuario


def require_roles(*allowed_roles: RolUsuario) -> Callable[..., Usuario]:
    """Dependency factory enforcing server-side role-based access control (RN-AU-02, RN-GL-01)."""
    allowed_set = frozenset(allowed_roles)

    def role_checker(
        current_user: Annotated[Usuario, Depends(get_current_user)],
    ) -> Usuario:
        if current_user.rol not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permisos para realizar esta acción",
            )
        return current_user

    return role_checker
