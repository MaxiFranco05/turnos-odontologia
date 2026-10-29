# Proposal: C-03 — Authentication & JWT Access Control (`c-03-auth-jwt`)

## Why

With the core domain models (`Usuario`, `PlantillaDisponibilidad`, `Turno`) and repository layer (`SqlAlchemyUsuarioRepository`) established in `C-02`, the backend still lacks an authentication mechanism and role-based access control (RBAC). Without JWT authentication and server-side role enforcement, downstream capabilities (`C-04` password reset, `C-06` appointment requests, `C-07` state transitions, `C-08`/`C-09`/`C-10` role agendas, and `C-12` login UI) cannot verify user identity or enforce the clinical data boundaries mandated by `RN-AU-01`, `RN-AU-02`, and `RN-GL-01`.

## What Changes

- **Credential Verification & Password Hashing**: Introduce bcrypt-based password hashing and verification utilities (`hash_password`, `verify_password`) in the infrastructure security layer.
- **JWT Token Issuing & Validation**: Implement HS256 JWT creation and decoding using `JWT_SECRET`, `JWT_ALGORITHM`, and `JWT_EXPIRE_MINUTES` from `Settings`, encoding `sub` (stringified `usuario.id`), `rol` (`paciente` | `recepcion` | `odontologo`), `debe_cambiar_password`, and `exp`.
- **Login Endpoint (`POST /api/auth/login`)**: Accept `identificador` (either `email` or `nro_socio`, resolved via `SqlAlchemyUsuarioRepository.get_by_identifier`) and `password`. Return `access_token`, `token_type="bearer"`, `rol`, and `debe_cambiar_password` (`password_change_required` indicator for `US-010` / `C-12`). Return a generic `401 Unauthorized` message (`"Credenciales inválidas"`) on unknown identifier or wrong password without leaking user existence (`RN-AU-01`).
- **Login Rate Limiting**: Enforce an in-memory sliding-window rate limiter of 5 requests per 60 seconds keyed by `(client_ip, identificador)` on `POST /api/auth/login`, returning `429 Too Many Requests` when exceeded.
- **Authentication Dependency (`get_current_user`)**: Validate the `Authorization: Bearer <token>` header, decode and verify JWT expiration and claims, load the `Usuario` entity from the database, and attach it to `request.state.user`. Return `401 Unauthorized` on missing, malformed, expired, or unresolvable tokens.
- **RBAC Dependency Factory (`require_roles(*roles)`)**: Validate that the authenticated `Usuario.rol` belongs to the allowed set of `RolUsuario` values for an endpoint, rejecting unauthorized roles with `403 Forbidden` (`RN-AU-02`, `RN-GL-01`).

## Capabilities

### New Capabilities
- `jwt-authentication`: User login with `email` or `nro_socio` (`POST /api/auth/login`), bcrypt password verification, JWT token generation with role and password-change flags, generic error messaging on invalid credentials, and 5 req/60s rate limiting per IP and identifier.
- `rbac-authorization`: Bearer JWT verification via `get_current_user` (populating `request.state.user`) and role-based endpoint protection via `require_roles(*roles)` enforcing HTTP 401 and 403 boundaries.

### Modified Capabilities
<!-- No existing capability requirements are modified. -->

## Impact

- **Dependencies**: Adds `python-jose[cryptography]` and `bcrypt` (or `passlib[bcrypt]`) to `backend/pyproject.toml` and `backend/requirements.txt`.
- **Backend Infrastructure**: Adds `backend/app/infrastructure/security.py` (password hashing, JWT encode/decode, login rate limiter).
- **Backend API & Schemas**: Adds `backend/app/api/deps.py` (`get_current_user`, `require_roles`), `backend/app/api/auth.py` (`POST /api/auth/login` with strict Pydantic `extra="forbid"` schemas), and registers the auth router in `backend/app/main.py`.
- **Tests**: Adds integration test suite `backend/tests/test_auth.py` exercising real database sessions (no DB mocks, per Hard Rule #7) across valid login (`email` and `nro_socio`), invalid credentials, expired/invalid tokens, RBAC role rejection (`403`), and login rate limiting (`429`).
