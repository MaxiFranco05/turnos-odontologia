# Design: C-03 — Authentication & JWT Access Control (`c-03-auth-jwt`)

## Context

See `proposal.md` — Why for the problem statement and motivation.

Current backend state after `C-01` and `C-02`:
- `backend/app/infrastructure/config.py` defines `Settings` (`extra="forbid"`) with `JWT_SECRET: str`, `JWT_ALGORITHM: str = "HS256"`, and `JWT_EXPIRE_MINUTES: int = 60`, exposed via `request.app.state.settings` and `get_settings()`.
- `backend/app/domain/models/usuario.py` defines `Usuario` (`id`, `nombre`, `email`, `nro_socio`, `password_hash`, `debe_cambiar_password`, `perfil_completo`, `rol: RolUsuario`).
- `backend/app/infrastructure/repositories/usuario.py` already provides `SqlAlchemyUsuarioRepository.get_by_identifier(identifier: str)` using SQLAlchemy 2.0 `select(Usuario).where(or_(Usuario.email == identifier, Usuario.nro_socio == identifier))` (Hard Rule #2).
- `backend/app/infrastructure/database.py` provides `get_db(request: Request) -> AsyncGenerator[AsyncSession, None]`.
- `backend/pyproject.toml` and `backend/requirements.txt` do not yet include JWT or bcrypt libraries.

Project hard rules constraining this design:
- **Hard Rule #1**: Every Pydantic request/response model MUST declare `model_config = ConfigDict(extra="forbid")`.
- **Hard Rule #2**: All DB queries MUST use SQLAlchemy 2.0 `select()`.
- **Hard Rule #3**: Functions without real async I/O (`hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, rate-limit checks) MUST be synchronous `def`, while DB-backed dependencies (`get_current_user`) and endpoints (`login`) use `async def`.
- **Hard Rule #7**: No DB mocks in tests — all authentication and RBAC tests run against a real database engine.
- **Hard Rule #8**: Noun-based REST paths (`/api/auth/login` is the explicit contract defined in `CHANGES.md` and `knowledge-base/08_arquitectura_propuesta.md`).

## Goals / Non-Goals

**Goals:**
- Provide stateless HS256 JWT token generation and validation configurable per FastAPI app instance (`request.app.state.settings`).
- Provide reusable FastAPI dependencies (`get_current_user`, `require_roles(*roles)`) that attach `Usuario` to `request.state.user` and enforce `401` / `403` boundaries.
- Enforce `5 req / 60s` rate limiting per `(client_ip, identificador)` on `POST /api/auth/login` without requiring Redis in v1.
- Prevent user enumeration (`RN-AU-01`) and timing discrepancies on invalid identifier vs. invalid password.

**Non-Goals:**
- Mandatory password change endpoint and enforcement guard (`C-04` `password-reset-flow` owns `/api/auth/cambiar-password` and the `debe_cambiar_password` blocking middleware).
- Redis-backed distributed rate limiting or token revocation blocklists (Redis is deferred to v2 per `AGENTS.md`).
- Frontend login UI (`C-12` `login-page`).

## UI Mockups

Decision: no (no UI)

## Decisions

### 1. Password Hashing: Direct `bcrypt` + `passlib[bcrypt]` compatibility
- **Choice**: Use `bcrypt` directly (or `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")` with `bcrypt<4.1` pinned alongside `python-jose[cryptography]`) inside synchronous helpers `hash_password(plain: str) -> str` and `verify_password(plain: str, hashed: str) -> bool` in `backend/app/infrastructure/security.py`.
- **Rationale**: `passlib 1.7.4` raises attribute errors on `bcrypt >= 4.1.0` (`__about__` removal and 72-byte check changes). Pinning `bcrypt>=4.0.1,<4.1.0` with `passlib[bcrypt]>=1.7.4` (as specified in `CHANGES.md` C-01/C-03) guarantees full compatibility with `passlib` while keeping standard `$2b$` bcrypt hashes.
- **Timing safety on missing user**: When `get_by_identifier` returns `None`, `login` still executes a dummy `verify_password` against a precomputed constant bcrypt hash before raising `401 Credenciales inválidas`, preventing timing-based user enumeration (`RN-AU-01`).
- **Alternatives considered**: Argon2 (`argon2-cffi`) — rejected because `CHANGES.md` explicitly specifies bcrypt via `passlib`.

### 2. JWT Library & Payload Structure (`python-jose[cryptography]`)
- **Choice**: Use `jose.jwt.encode` and `jose.jwt.decode` with `HS256` in `backend/app/infrastructure/security.py`.
- **Claims**:
  - `sub`: `str(usuario.id)` (RFC 7519 requires `sub` to be a string).
  - `rol`: `usuario.rol.value` (`"paciente"`, `"recepcion"`, or `"odontologo"`).
  - `debe_cambiar_password`: `bool(usuario.debe_cambiar_password)`.
  - `exp`: UTC timestamp (`datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)`).
- **Login Response Schema (`TokenResponse`)**:
  - `access_token: str`
  - `token_type: str = "bearer"`
  - `rol: RolUsuario`
  - `debe_cambiar_password: bool`
- **Rationale**: Including `rol` and `debe_cambiar_password` both in the JWT claims and top-level login response allows `C-12` (`login-page`) and `C-04` (`password-reset-flow`) to inspect role and password-change status immediately upon login without an extra round-trip.

### 3. FastAPI Dependencies (`get_current_user` and `require_roles`)
- **Choice**: Implement in `backend/app/api/deps.py`:
  - `oauth2_scheme = HTTPBearer(auto_error=False)` (using `fastapi.security.HTTPBearer` so missing/invalid headers consistently return `401 Unauthorized` with `WWW-Authenticate: Bearer`, instead of FastAPI's default `403` in older `HTTPBearer(auto_error=True)` versions).
  - `async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Usuario`:
    1. Rejects missing or non-Bearer credentials with `401`.
    2. Reads `settings` from `request.app.state.settings` (falling back to `get_settings()`).
    3. Calls synchronous `decode_access_token(token, settings)`. Raises `401` on `JWTError` or expired token or non-integer `sub`.
    4. Queries `SqlAlchemyUsuarioRepository(db).get_by_id(int(sub))`. Raises `401` if `None`.
    5. Sets `request.state.user = usuario` and returns `usuario`.
  - `def require_roles(*allowed_roles: RolUsuario) -> Callable`:
    Returns an inner dependency `def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario` (synchronous `def` per Hard Rule #3 since it performs no async I/O of its own) that checks `current_user.rol in allowed_roles` and raises `HTTPException(status_code=403, detail="Sin permisos para realizar esta acción")` when unauthorized.
- **Alternatives considered**: Starlette `BaseHTTPMiddleware` — rejected because FastAPI `Depends` integrates cleanly with OpenAPI security schemas, `get_db` lifecycle, and route-level `require_roles`.

### 4. In-Memory Sliding-Window Rate Limiter for Login
- **Choice**: Implement a synchronous `LoginRateLimiter` class in `backend/app/infrastructure/security.py` using `collections.defaultdict(collections.deque)` and `time.monotonic()`, stored on `app.state.login_rate_limiter` (initialized in `create_app`).
- **Keying**: `(client_ip, payload.identificador.strip().lower())`, where `client_ip` is extracted from `request.client.host` (or `"unknown"`).
- **Window**: Max `5` requests within `60.0` seconds. Before processing `POST /api/auth/login`, evict timestamps older than `now - 60.0`; if `len(timestamps) >= 5`, raise `HTTPException(status_code=429, detail="Demasiados intentos de inicio de sesión. Intente nuevamente en un minuto.")`; otherwise append `now`.
- **Rationale**: Zero external infrastructure required in v1 (Redis is v2+), deterministic in tests (can be reset or injected via `app.state.login_rate_limiter`), and O(1) amortized memory/time per attempt.

## Risks / Trade-offs

- **[Risk] In-memory rate limiter state is per-process** → Mitigation: Acceptable for v1 single-container deployment defined in `02_descripcion_general.md`; `LoginRateLimiter` interface is isolated in `security.py` so v2 can swap in Redis without changing `auth.py`.
- **[Risk] `passlib` + `bcrypt>=4.1` incompatibility in Docker builds** → Mitigation: Pin `bcrypt>=4.0.1,<4.1.0` in `backend/pyproject.toml` and `backend/requirements.txt` and verify via test suite.
- **[Risk] Deleted user with still-valid JWT** → Mitigation: `get_current_user` loads `Usuario` from DB via `get_by_id` on every authenticated request, immediately rejecting tokens for deleted users with `401`.

## Migration Plan

- No database schema migration is required (`usuarios` table from `002_create_core_tables.py` already has `email`, `nro_socio`, `password_hash`, `rol`, and `debe_cambiar_password`).
- Install updated Python dependencies (`python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt<4.1.0`, `aiosqlite`).
