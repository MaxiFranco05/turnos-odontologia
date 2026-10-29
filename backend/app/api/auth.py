from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.models.enums import RolUsuario
from app.domain.models.usuario import Usuario
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.usuario import SqlAlchemyUsuarioRepository
from app.infrastructure.security import (
    DUMMY_PASSWORD_HASH,
    LoginRateLimiter,
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_default_rate_limiter = LoginRateLimiter()


class LoginRequest(BaseModel):
    """Strict request schema for user authentication (Hard Rule #1: extra='forbid')."""

    model_config = ConfigDict(extra="forbid")

    identificador: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Strict request schema for mandatory first-login password change (Hard Rule #1: extra='forbid')."""

    model_config = ConfigDict(extra="forbid")

    password_actual: str = Field(min_length=1, max_length=255)
    password_nueva: str = Field(min_length=8, max_length=255)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=255)

    @field_validator("password_nueva")
    @classmethod
    def _validate_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class TokenResponse(BaseModel):
    """Strict response schema for issued JWT access token (Hard Rule #1: extra='forbid')."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    rol: RolUsuario
    debe_cambiar_password: bool
    perfil_completo: bool = False


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
        perfil_completo=usuario.perfil_completo,
    )


async def _execute_mandatory_password_change(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: Usuario,
    db: AsyncSession,
) -> TokenResponse:
    """Shared implementation for mandatory first-login password change and profile completeness check."""
    if not current_user.debe_cambiar_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no requiere cambio obligatorio de contraseña",
        )

    if not verify_password(payload.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    if payload.password_nueva == payload.password_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual",
        )

    repo = SqlAlchemyUsuarioRepository(db)

    if payload.email is not None:
        clean_email = payload.email.strip()
        if clean_email != current_user.email:
            existing = await repo.get_by_email(clean_email)
            if existing is not None and existing.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo electrónico ya está registrado por otro usuario",
                )
            current_user.email = clean_email

    if payload.nombre is not None:
        current_user.nombre = payload.nombre.strip()

    current_user.password_hash = hash_password(payload.password_nueva)
    current_user.debe_cambiar_password = False
    current_user.perfil_completo = bool(
        current_user.nombre
        and current_user.nombre.strip()
        and current_user.email
        and current_user.email.strip()
    )

    await db.flush()

    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    token = create_access_token(
        user_id=current_user.id,
        rol=current_user.rol,
        debe_cambiar_password=current_user.debe_cambiar_password,
        settings=settings,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=current_user.rol,
        debe_cambiar_password=current_user.debe_cambiar_password,
        perfil_completo=current_user.perfil_completo,
    )


@router.post("/cambiar-password", response_model=TokenResponse)
async def cambiar_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Completes mandatory first-login password replacement (US-010)."""
    return await _execute_mandatory_password_change(payload, request, current_user, db)


@router.post("/password", response_model=TokenResponse)
async def replace_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Noun-based REST alias for mandatory first-login password replacement (Hard Rule #8)."""
    return await _execute_mandatory_password_change(payload, request, current_user, db)
