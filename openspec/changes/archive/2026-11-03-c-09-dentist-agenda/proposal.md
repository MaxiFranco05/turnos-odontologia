# Proposal: C-09 — Dentist Daily Agenda (`c-09-dentist-agenda`)

## Why

With appointment creation (`C-06`) and lifecycle state transitions (`C-07`) completed, dentists can already mark their confirmed appointments as `presente` or `ausente` (`PATCH /api/turnos/{id}`). However, the backend lacks the read-only daily agenda endpoint (`GET /api/mis-turnos?fecha=YYYY-MM-DD`) required by **US-007 ("Ver mis turnos — odontólogo")** and **Flujo 4** so an authenticated dentist can view their own appointments for a given clinic date (`America/Argentina/Buenos_Aires`) without ever seeing another professional's appointments (`RN-AU-02`, `RN-GL-01`). Implementing `C-09` unlocks the frontend dentist view (`C-15` at **GATE 6**).

## What Changes

- **Dentist Daily Agenda Endpoint (`GET /api/mis-turnos?fecha=YYYY-MM-DD`)**:
  - Exposes `GET /api/mis-turnos` in `backend/app/api/mis_turnos.py` (registered in `backend/app/main.py`), designed as the unified self-agenda resource path shared with `C-10` (`patient-portal`). In `C-09`, access is restricted to `Depends(require_roles(RolUsuario.ODONTOLOGO))` (enforcing JWT authentication, `rol == "odontologo"`, and `debe_cambiar_password == False` per `US-010`, `RN-AU-02`, and `RN-GL-01`).
  - Automatically binds `odontologo_id = current_user.id` from the JWT token (OWASP API1:2023 BOLA/IDOR protection — no `odontologo_id` query parameter is accepted, so a dentist can never query another dentist's agenda).
  - Accepts required query parameter `fecha: datetime.date` (`YYYY-MM-DD`), computes the clinic day window `[00:00:00, 24:00:00)` in `settings.TIMEZONE` (`America/Argentina/Buenos_Aires`), and queries `SqlAlchemyTurnoRepository.find_by_dentist_range(odontologo_id=current_user.id, start=day_start, end=day_end)` (**Hard Rule #2**: SQLAlchemy 2.0 `select()`).
  - Returns all appointments for that dentist on the requested clinic day across all lifecycle states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`) ordered ascending by `inicio`, enriched with a nested `PacienteResumenResponse` (`id`, `nombre`, `nro_socio`, `email` — omitting sensitive fields like `password_hash`, `debe_cambiar_password`, `rol`) under strict `ConfigDict(extra="forbid", from_attributes=True)` (**Hard Rule #1**).
- **Roadmap Sync (`CHANGES.md`)**:
  - Updates `C-15` (`dentist-features`) in `CHANGES.md` to reference the canonical `PATCH /api/turnos/{id}` (`{"estado": "presente" | "ausente"}`) from `C-07` instead of the legacy verb subpath `PATCH /marcar-presente|ausente` (**Hard Rules #8 and #9**).

## Capabilities

### New Capabilities
- `dentist-agenda`: Authenticated dentist daily self-agenda query (`GET /api/mis-turnos?fecha=YYYY-MM-DD`) enforcing strict server-side ownership isolation (`odontologo_id == current_user.id`, `RN-AU-02`, `RN-GL-01`), clinic timezone day boundaries (`America/Argentina/Buenos_Aires`), chronological sorting by `inicio`, and nested non-sensitive patient identification (`US-007`, `Flujo 4`).

### Modified Capabilities
<!-- No existing capability requirements are modified. -->

## Impact

- **Application Layer**: Adds pure synchronous helper `def get_clinic_day_bounds(fecha: datetime.date, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (**Hard Rule #3**: synchronous `def`, zero I/O, zero `infrastructure` imports).
- **API Layer**: Adds `backend/app/api/mis_turnos.py` with `PacienteResumenResponse` and `MisTurnosOdontologoItemResponse` (`ConfigDict(extra="forbid", from_attributes=True)`, **Hard Rule #1**) and `GET /api/mis-turnos` (**Hard Rule #8**), wired into `backend/app/main.py`.
- **Tests**: Adds `backend/tests/test_dentist_agenda.py` testing multi-dentist isolation (`US-007 CA-1`, OWASP BOLA), all lifecycle states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`), chronological ordering, clinic-day boundary filtering, RBAC rejections (`401`, `403` for `paciente`/`recepcion`/`debe_cambiar_password=True`), and `422` missing/invalid `fecha` against real in-memory SQLite (**Hard Rule #7**) with 100% synthetic data (**Hard Rule #12**).
