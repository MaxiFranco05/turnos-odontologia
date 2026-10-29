# Proposal: C-04 — Mandatory Password Reset Flow (`c-04-password-reset-flow`)

## Why

Patient and staff accounts provisioned by reception (`DD-07`, `US-010`) start with a temporary password and `debe_cambiar_password=True`. While `C-03` (`auth-jwt`) issues JWT tokens carrying `debe_cambiar_password`, the system does not yet provide an endpoint to replace the temporary password, enforce password strength rules, update `perfil_completo`, or block other operations (`US-010 CA-2`) and redirect the client to `/cambiar-password` until the mandatory password change is completed.

## What Changes

- **Mandatory Password Change Endpoint (`POST /api/auth/cambiar-password` & `/api/auth/password`)**:
  - Require an authenticated user whose account currently has `debe_cambiar_password=True` (reject with `400 Bad Request` if `debe_cambiar_password=False`).
  - Verify `password_actual` against the stored bcrypt `password_hash` (reject with `400 Bad Request` if invalid).
  - Validate `password_nueva` strength: minimum 8 characters, at least 1 uppercase letter (`A-Z`), at least 1 digit (`0-9`), and must differ from `password_actual`.
  - Optionally accept profile completion fields (`nombre`, `email`), persist the new bcrypt `password_hash`, set `debe_cambiar_password = False`, and set `perfil_completo = True` when minimum required profile data (`nombre` non-empty and at least one of `email` or `nro_socio` present, or `email` provided) are satisfied (`US-010 CA-3`).
  - Return a fresh `TokenResponse` (`access_token` with `debe_cambiar_password=False`, `token_type="bearer"`, `rol`, `debe_cambiar_password=False`, `perfil_completo`).
- **Server-Side Blocking Guard while `debe_cambiar_password=True` (`US-010 CA-2`)**:
  - Update `require_roles(*roles)` (and provide `require_password_changed`) in `backend/app/api/deps.py` so any authenticated user with `debe_cambiar_password=True` attempting to access protected role-restricted endpoints is rejected with HTTP `403 Forbidden` and `detail="password_change_required"`.
- **Frontend API Interceptor & Router Guard (`frontend/`)**:
  - Update the Axios response interceptor in `frontend/src/lib/api.ts` to detect HTTP `403` or `400` responses with `detail === "password_change_required"` (or `code === "password_change_required"`) and redirect/notify to `/cambiar-password` without clearing the stored JWT access token.
  - Update `ProtectedRoute` (`frontend/src/router/ProtectedRoute.tsx`) and `routes.tsx` (`frontend/src/router/routes.tsx`) to register `/cambiar-password` and automatically redirect any authenticated user with `debe_cambiar_password: true` to `/cambiar-password` before accessing any role view.

## Capabilities

### New Capabilities
- `password-reset-flow`: Mandatory first-login password change endpoint (`POST /api/auth/cambiar-password`), current password verification, password strength validation (min 8 chars, ≥1 uppercase, ≥1 number), deactivation of `debe_cambiar_password`, and `perfil_completo` calculation (`US-010`).

### Modified Capabilities
- `rbac-authorization`: Reject protected role-restricted operations with HTTP `403 Forbidden` (`detail: "password_change_required"`) when the authenticated user still has `debe_cambiar_password=True` (`US-010 CA-2`).
- `frontend-api-client`: Intercept HTTP `403`/`400` `"password_change_required"` responses and redirect to `/cambiar-password` while preserving the active JWT token.
- `frontend-application-shell`: Add `/cambiar-password` route and enforce route-level redirection to `/cambiar-password` in `ProtectedRoute` whenever `user.debe_cambiar_password` is `true`.

## Impact

- **Backend (`backend/`)**:
  - `backend/app/infrastructure/security.py`: Synchronous password strength validator (`validate_password_strength`).
  - `backend/app/api/auth.py`: `ChangePasswordRequest` (`extra="forbid"`), updated response schema, and `POST /api/auth/cambiar-password` (plus noun alias `/api/auth/password`).
  - `backend/app/api/deps.py`: `debe_cambiar_password` check inside `require_roles` raising `403` `"password_change_required"`.
  - `backend/tests/test_password_reset.py`: Real-DB integration tests covering first-time password change, strength validation, flag persistence until change, `perfil_completo` update, and `403` blocking of protected endpoints while `debe_cambiar_password=True`.
- **Frontend (`frontend/`)**:
  - `frontend/src/types/auth.ts`: Add `debe_cambiar_password?: boolean` and `perfil_completo?: boolean` to `UserProfile`.
  - `frontend/src/lib/api.ts` & `frontend/src/lib/api.test.ts`: Handle `403`/`400` `"password_change_required"` -> redirect to `/cambiar-password`.
  - `frontend/src/router/ProtectedRoute.tsx`, `frontend/src/router/routes.tsx`, & `frontend/src/router/router.test.tsx`: Enforce mandatory redirect to `/cambiar-password` when `user.debe_cambiar_password === true`.
