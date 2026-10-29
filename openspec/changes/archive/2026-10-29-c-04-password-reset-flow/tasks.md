# Tasks: C-04 — Mandatory Password Reset Flow (`c-04-password-reset-flow`)

## 1. Backend Password Strength & Blocking Guard (`security.py`, `deps.py`)

- [x] 1.1 Following Strict TDD, write unit and integration tests in `backend/tests/test_password_reset.py` for synchronous `validate_password_strength` (`>=8` chars, `>=1` uppercase, `>=1` digit) and for `require_roles` / `require_password_changed` rejecting users with `debe_cambiar_password=True` with HTTP `403 Forbidden` and `detail="password_change_required"` (`US-010 CA-2`).
- [x] 1.2 Implement `validate_password_strength` in `backend/app/infrastructure/security.py` and the `debe_cambiar_password` enforcement in `backend/app/api/deps.py`, and verify all tests in `backend/tests/test_password_reset.py` and `backend/tests/test_auth.py` pass via `pytest`.

## 2. Backend Mandatory Password Change Endpoint (`POST /api/auth/cambiar-password`)

- [x] 2.1 Following Strict TDD, write real-DB integration tests (no DB mocks, Hard Rule #7) in `backend/tests/test_password_reset.py` covering: successful first-time password change turning off `debe_cambiar_password=False` and updating `perfil_completo=True` when minimum profile data (`nombre` and `email`) are present; keeping `perfil_completo=False` when `email` remains absent; rejecting requests when `debe_cambiar_password=False` (`400`); rejecting wrong `password_actual` (`400`); rejecting weak or unchanged `password_nueva` (`422`/`400`); rejecting extra undeclared fields (`422`, `extra="forbid"`); and unlocking protected role endpoints after completing the password change.
- [x] 2.2 Implement `ChangePasswordRequest` (`extra="forbid"`), update `TokenResponse` (adding `perfil_completo: bool = False`), and register `POST /api/auth/cambiar-password` (plus noun alias `POST /api/auth/password`) in `backend/app/api/auth.py`, verifying the full backend test suite (`pytest backend/tests`) passes with zero regressions.

## 3. Frontend Interceptor & Router Guard (`api.ts`, `ProtectedRoute.tsx`, `routes.tsx`)

- [x] 3.1 Following Strict TDD, write Vitest tests in `frontend/src/lib/api.test.ts` and `frontend/src/router/router.test.tsx` verifying that: (a) HTTP `403`/`400` responses with `detail: "password_change_required"` preserve the stored JWT token and invoke the password-change redirection to `/cambiar-password` without triggering generic permission alerts; and (b) `ProtectedRoute` redirects any authenticated user with `debe_cambiar_password: true` to `/cambiar-password` while allowing access once `debe_cambiar_password: false`.
- [x] 3.2 Update `frontend/src/types/auth.ts`, `frontend/src/lib/api.ts`, `frontend/src/router/ProtectedRoute.tsx`, and `frontend/src/router/routes.tsx` to implement the interceptor and `/cambiar-password` route guard, and verify all frontend Vitest tests (`npm test` in `frontend/`) pass.

## Workflow follow-up

- Run `openspec validate c-04-password-reset-flow --strict` to confirm spec and change validity.
- Archive the change with `/opsx:archive c-04-password-reset-flow` and mark `[x]` on `C-04` in `CHANGES.md` after implementation review is satisfied.
