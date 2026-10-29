from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import time
from typing import Any

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from app.domain.models.enums import RolUsuario
from app.infrastructure.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hashes a plain-text password using bcrypt (synchronous per Hard Rule #3)."""
    return str(pwd_context.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain-text password against a bcrypt hash (synchronous per Hard Rule #3)."""
    try:
        return bool(pwd_context.verify(plain, hashed))
    except Exception:
        return False


# Precomputed hash used when identifier does not exist to prevent timing-based user enumeration (RN-AU-01)
DUMMY_PASSWORD_HASH: str = hash_password("dummy_timing_protection_secret")


def create_access_token(
    *,
    user_id: int,
    rol: RolUsuario | str,
    debe_cambiar_password: bool,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Issues a signed HS256 JWT containing sub, rol, debe_cambiar_password, and exp."""
    rol_value = rol.value if isinstance(rol, RolUsuario) else str(rol)
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    expire = datetime.now(timezone.utc) + delta
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "rol": rol_value,
        "debe_cambiar_password": bool(debe_cambiar_password),
        "exp": expire,
    }
    return str(
        jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
    )


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decodes and validates a signed JWT token (raises jose.JWTError on invalid/expired token)."""
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload


class LoginRateLimiter:
    """In-memory sliding-window rate limiter keyed by (client_ip, normalized_identifier)."""

    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check_or_raise(self, client_ip: str, identificador: str) -> None:
        """Checks if (client_ip, identificador) exceeded max_requests within window_seconds."""
        now = self._clock()
        cutoff = now - self.window_seconds
        key = (client_ip, identificador.strip().lower())
        timestamps = self._attempts[key]

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos de inicio de sesión. Intente nuevamente en un minuto.",
            )

        timestamps.append(now)

    def reset(self) -> None:
        """Clears all recorded login attempts."""
        self._attempts.clear()
