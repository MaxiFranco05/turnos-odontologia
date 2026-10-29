from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import RolUsuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository
from app.infrastructure.security import (
    DUMMY_PASSWORD_HASH,
    LoginRateLimiter,
    create_access_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_default_rate_limiter = LoginRateLimiter()


class LoginRequest(BaseModel):
    """Strict request schema for user authentication (Hard Rule #1: extra='forbid')."""

    model_config = ConfigDict(extra="forbid")

    identificador: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Strict response schema for issued JWT access token (Hard Rule #1: extra='forbid')."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    rol: RolUsuario
    debe_cambiar_password: bool


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticates a user by email or nro_socio and returns a signed JWT access token."""
    client_ip = request.client.host if request.client else "unknown"
    limiter: LoginRateLimiter = (
        getattr(request.app.state, "login_rate_limiter", None) or _default_rate_limiter
    )
    limiter.check_or_raise(client_ip, payload.identificador)

    repo = SqlAlchemyUsuarioRepository(db)
    usuario = await repo.get_by_identifier(payload.identificador.strip())

    if usuario is None:
        # Constant-time dummy check to prevent timing-based user enumeration (RN-AU-01)
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    token = create_access_token(
        user_id=usuario.id,
        rol=usuario.rol,
        debe_cambiar_password=usuario.debe_cambiar_password,
        settings=settings,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=usuario.rol,
        debe_cambiar_password=usuario.debe_cambiar_password,
    )
