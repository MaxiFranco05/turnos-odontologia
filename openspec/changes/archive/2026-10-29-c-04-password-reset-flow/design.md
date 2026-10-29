# Design: C-04 — Mandatory Password Reset Flow (`c-04-password-reset-flow`)

## Context

See `proposal.md` — Why for the problem statement and motivation.

Current state after `C-03` (`auth-jwt`) and `C-11` (`frontend-scaffold`):
- `Usuario` (`backend/app/domain/models/usuario.py`) has `nombre`, `email`, `nro_socio`, `password_hash`, `debe_cambiar_password: bool = True`, `perfil_completo: bool = False`, and `rol: RolUsuario`.
- `POST /api/auth/login` (`backend/app/api/auth.py`) issues JWT access tokens with `sub`, `rol`, `debe_cambiar_password`, and `exp`, and returns `TokenResponse` containing `debe_cambiar_password`.
- `get_current_user` and `require_roles(*allowed_roles)` (`backend/app/api/deps.py`) authenticate the Bearer token and enforce role access, but do not yet block users who still have `debe_cambiar_password=True`.
- `frontend/src/lib/api.ts` intercepts `401` and `403`, and `frontend/src/router/ProtectedRoute.tsx` enforces authentication and role checks, but neither intercepts `"password_change_required"` nor redirects users with `debe_cambiar_password=true` to `/cambiar-password`.

## Goals / Non-Goals

**Goals:**
- Implement `POST /api/auth/cambiar-password` (and noun-based alias `POST /api/auth/password` for Hard Rule #8 compliance) enforcing `debe_cambiar_password=True`, current password verification, password strength validation (≥8 chars, ≥1 uppercase, ≥1 digit, different from current), `debe_cambiar_password=False`, and `perfil_completo` evaluation.
- Block role-protected endpoints when `current_user.debe_cambiar_password is True` with HTTP `403 Forbidden` and `detail="password_change_required"` (`US-010 CA-2`).
- Intercept `403`/`400` `"password_change_required"` in `frontend/src/lib/api.ts` and enforce route redirection to `/cambiar-password` in `ProtectedRoute.tsx` and `routes.tsx`.

**Non-Goals:**
- Unauthenticated "forgot password via email link" recovery (out of scope in `06_funcionalidades.md` and `CHANGES.md`; `C-04` is strictly the first-login mandatory password replacement flow `US-010`).
- Full interactive login page and password-change form submission UI (`C-12` `login-page` connects the login and password change forms to the backend endpoints).

## UI Mockups

Decision: no (C-04 implements the backend password reset endpoint/guards and the frontend HTTP interceptor + router guard redirect to `/cambiar-password`; visual form pages belong to `C-12`).

## Decisions

### 1. Endpoint Path & Request/Response Contract (`POST /api/auth/cambiar-password` & `/api/auth/password`)
- **Choice**: Register both `@router.post("/cambiar-password")` (explicitly required by `CHANGES.md` C-04) and `@router.post("/password")` (noun-based URI per Hard Rule #8) on `backend/app/api/auth.py`.
- **Request Schema (`ChangePasswordRequest`)**:
  - `model_config = ConfigDict(extra="forbid")` (Hard Rule #1).
  - `password_actual: str = Field(min_length=1)`
  - `password_nueva: str = Field(min_length=8)`
  - `nombre: str | None = Field(default=None, min_length=1, max_length=120)`
  - `email: str | None = Field(default=None, min_length=3, max_length=255)`
- **Validation & State Transitions**:
  1. Require authenticated user via `Depends(get_current_user)`.
  2. If `not current_user.debe_cambiar_password`, raise `HTTPException(status_code=400, detail="El usuario no requiere cambio obligatorio de contraseña")`.
  3. Verify `verify_password(payload.password_actual, current_user.password_hash)`. If `False`, raise `HTTPException(status_code=400, detail="La contraseña actual es incorrecta")`.
  4. Validate `password_nueva` via synchronous `validate_password_strength(payload.password_nueva)` (`len >= 8`, at least one `[A-Z]`, at least one `[0-9]`). If invalid, raise `HTTPException(status_code=422, detail=...)` (or Pydantic `@field_validator` raising `ValueError` → `422`).
  5. If `payload.password_nueva == payload.password_actual`, raise `HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")`.
  6. Update `nombre` and `email` on `current_user` if provided in payload.
  7. Set `current_user.password_hash = hash_password(payload.password_nueva)` and `current_user.debe_cambiar_password = False`.
  8. Evaluate `current_user.perfil_completo = bool(current_user.nombre and current_user.nombre.strip() and current_user.email and current_user.email.strip())`.
  9. Flush changes via `db.flush()` (the `get_db_session` dependency commits on exit) and return `TokenResponse` with a freshly minted JWT access token (`debe_cambiar_password=False`) and `perfil_completo=current_user.perfil_completo`.

### 2. Server-Side Blocking of Protected Operations while `debe_cambiar_password=True`
- **Choice**: Enforce the check inside `require_roles(*allowed_roles)` in `backend/app/api/deps.py` (and expose a reusable synchronous dependency `require_password_changed(current_user: Usuario = Depends(get_current_user)) -> Usuario`):
  - Inside `role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario`:
    1. First check `if current_user.debe_cambiar_password:` → `raise HTTPException(status_code=403, detail="password_change_required")`.
    2. Then check `if current_user.rol not in allowed_roles:` → `raise HTTPException(status_code=403, detail="Sin permisos para realizar esta acción")`.
- **Rationale**:
  - `get_current_user` remains usable by `POST /api/auth/cambiar-password` (which *requires* `debe_cambiar_password=True`) and preserves backward compatibility with existing unit tests of `get_current_user` in `test_auth.py`.
  - Every business endpoint in `C-05` through `C-10` uses `require_roles(...)` (or `require_password_changed`), guaranteeing that no operation can be performed while `debe_cambiar_password=True` (`US-010 CA-2`).
  - `role_checker` and `require_password_changed` perform no async I/O and remain synchronous `def` functions (Hard Rule #3).

### 3. Frontend Interceptor (`api.ts`) & Route Guard (`ProtectedRoute.tsx`)
- **Choice**:
  - In `frontend/src/lib/api.ts`:
    - Add a configurable `passwordChangeRequiredHandler` (`setPasswordChangeRequiredHandler`) alongside `unauthorizedHandler` and `forbiddenHandler`.
    - In the response error interceptor, before handling generic `403` permission errors, check if `(status === 403 || status === 400)` and `data?.detail === 'password_change_required'` (or `data?.code === 'password_change_required'`).
    - When matched: keep the JWT token in `localStorage` intact, invoke `passwordChangeRequiredHandler()` if registered, and redirect `window.location.href = '/cambiar-password'` if not already on `/cambiar-password`. Do not trigger the generic `forbiddenHandler`.
  - In `frontend/src/types/auth.ts`:
    - Add `debe_cambiar_password?: boolean` and `perfil_completo?: boolean` to `UserProfile`.
  - In `frontend/src/router/ProtectedRoute.tsx` and `frontend/src/router/routes.tsx`:
    - Register `/cambiar-password` under `AuthLayout` (or protected route allowing pending password change).
    - In `ProtectedRoute`: if `activeUser.debe_cambiar_password === true` and `location.pathname !== '/cambiar-password'`, return `<Navigate to="/cambiar-password" replace />`.

## Risks / Trade-offs

- **[Risk] Client keeps old JWT in memory after changing password** → Mitigation: `POST /api/auth/cambiar-password` returns a new `TokenResponse` (`access_token` with `debe_cambiar_password=False` and `perfil_completo`), AND the server-side check reads `current_user.debe_cambiar_password` from the database in `get_current_user`, so the updated flag takes effect immediately in the DB.
- **[Risk] Duplicate `email` submitted during profile completion** → Mitigation: Check `SqlAlchemyUsuarioRepository.get_by_email` if `payload.email` differs from `current_user.email` and return `400 Bad Request` instead of an unhandled `IntegrityError`.

## Migration Plan

- No Alembic schema migration is needed (`debe_cambiar_password` and `perfil_completo` already exist on `usuarios` in `002_create_core_tables.py`).
