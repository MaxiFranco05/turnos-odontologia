# Tasks: C-03 — Authentication & JWT Access Control (`c-03-auth-jwt`)

## 1. Dependencies & Security Infrastructure

- [x] 1.1 Add `python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt>=4.0.1,<4.1.0`, and `aiosqlite` to `backend/pyproject.toml` and `backend/requirements.txt`, and verify installation succeeds in the Python environment.
- [x] 1.2 Following Strict TDD, write unit/integration tests in `backend/tests/test_auth.py` for synchronous `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, and `LoginRateLimiter` (`backend/app/infrastructure/security.py`), then implement `security.py` and verify all tests pass via `pytest backend/tests/test_auth.py`.

## 2. Login Endpoint (`POST /api/auth/login`)

- [x] 2.1 Following Strict TDD, write integration tests in `backend/tests/test_auth.py` (using a real database engine, no DB mocks) covering login with `email`, login with `nro_socio`, JWT claim verification (`sub`, `rol`, `debe_cambiar_password`, `exp`), generic `401` error on invalid identifier or wrong password (`RN-AU-01`), `422` on extra undeclared fields (`extra="forbid"`), and `429` after 5 requests in 60s per `(client_ip, identificador)`.
- [x] 2.2 Implement `LoginRequest` and `TokenResponse` schemas (`extra="forbid"`) and `POST /api/auth/login` router in `backend/app/api/auth.py`, register the router and `app.state.login_rate_limiter` in `backend/app/main.py`, and verify all login and rate-limit tests in `backend/tests/test_auth.py` pass.

## 3. Authentication & RBAC Dependencies (`get_current_user`, `require_roles`)

- [x] 3.1 Following Strict TDD, write integration tests in `backend/tests/test_auth.py` for `get_current_user` (valid Bearer token attaches `Usuario` to `request.state.user`, missing/malformed token returns `401`, expired token returns `401`, deleted/non-existent user ID returns `401`) and `require_roles(*roles)` (permitted role succeeds with `200`, unpermitted role returns `403 Forbidden`).
- [x] 3.2 Implement `get_current_user` and `require_roles` in `backend/app/api/deps.py` and verify the full test suite (`pytest backend/tests`) passes with zero regressions.

## Workflow follow-up

- Run `openspec validate c-03-auth-jwt --strict` to confirm spec and change validity.
- Archive the change with `/opsx:archive c-03-auth-jwt` and mark `[x]` on `C-03` in `CHANGES.md` after implementation review is satisfied.
