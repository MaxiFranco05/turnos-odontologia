# Proposal: C-10 — Patient Portal Self-Appointments (`c-10-patient-portal`)

## Why

Patients can already browse free slots (`C-05`), request online appointments (`C-06`), and cancel their own future appointments with at least 24 hours' anticipation via `PATCH /api/turnos/{id}` (`C-07`). However, the backend still needs the patient-side self-appointment listing (`GET /api/mis-turnos?fecha_desde=&fecha_hasta=`) required by **US-004 ("Avisar ausentismo")** and **Flujo 5** so an authenticated `paciente` can view their own past and future appointments (with assigned dentist details) and never see another patient's appointments (`RN-GL-01`). Completing `C-10` unlocks the frontend patient views (`C-13` at **GATE 6**).

## What Changes

- **Unified Self-Appointments Endpoint Extended to `paciente` (`GET /api/mis-turnos`)**:
  - Extends `GET /api/mis-turnos` in `backend/app/api/mis_turnos.py` to allow both `RolUsuario.ODONTOLOGO` and `RolUsuario.PACIENTE` via `Depends(require_roles(RolUsuario.ODONTOLOGO, RolUsuario.PACIENTE))` (while keeping `RolUsuario.RECEPCION` forbidden with `403`, since Reception uses `GET /api/agenda/dia` in `C-08`).
  - When `current_user.rol == RolUsuario.PACIENTE`:
    - Automatically binds `paciente_id = current_user.id` from the JWT token (OWASP API1:2023 BOLA/IDOR protection — no `paciente_id` query parameter is accepted).
    - Accepts optional `fecha_desde: datetime.date | None` and `fecha_hasta: datetime.date | None` query parameters (`YYYY-MM-DD`). If `fecha_desde` and `fecha_hasta` are both provided and `fecha_hasta < fecha_desde`, rejects with HTTP `422 Unprocessable Entity`. If a `paciente` passes the dentist-only `fecha` parameter, rejects with HTTP `422 Unprocessable Entity` (and vice versa if an `odontologo` omits `fecha` or passes `fecha_desde`/`fecha_hasta`).
    - Computes the inclusive date range bounds `[start, end)` in `settings.TIMEZONE` (`America/Argentina/Buenos_Aires`) via a pure synchronous helper `def get_clinic_date_range_bounds(...)` in `backend/app/application/turnos.py` (**Hard Rule #3**), and queries `SqlAlchemyTurnoRepository.find_by_patient_range(paciente_id=current_user.id, start=range_start, end=range_end)` with explicit `.options(selectinload(Turno.odontologo))` (**Hard Rule #2** — zero N+1 queries).
    - Returns all matching appointments across all lifecycle states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`) sorted ascending by `inicio`, enriched with a nested least-privilege `OdontologoResumenResponse` (`id`, `nombre`, `nro_socio`, `email` — omitting `password_hash`, `debe_cambiar_password`, `rol`) under `ConfigDict(extra="forbid", from_attributes=True)` (**Hard Rule #1**, OWASP API3:2023 BOPLA).
- **Roadmap Sync (`CHANGES.md`)**:
  - Updates `C-13` (`patient-features`) in `CHANGES.md` to reference `PATCH /api/turnos/{id}` (`{"estado": "cancelado"}`) instead of the legacy verb subpath `PATCH /api/turnos/{id}/cancelar` (**Hard Rules #8 and #9**).

## Capabilities

### New Capabilities
- `patient-portal`: Authenticated patient self-appointment listing (`GET /api/mis-turnos?fecha_desde=&fecha_hasta=`) with optional inclusive clinic-timezone date filtering (`America/Argentina/Buenos_Aires`), strict BOLA ownership isolation (`paciente_id == current_user.id`), eager-loaded least-privilege `odontologo` summary, and end-to-end integration with `PATCH /api/turnos/{id}` (`{"estado": "cancelado"}`, `US-004`, `Flujo 5`).

### Modified Capabilities
- `dentist-agenda`: Updates the RBAC requirement on `GET /api/mis-turnos` so that `paciente` is now an authorized role on `/api/mis-turnos` (routed to the patient range view), while `recepcion` remains rejected with `403 Forbidden` and role-mismatched query parameters (`fecha` for `paciente`, or missing `fecha` for `odontologo`) return `422 Unprocessable Entity`.

## Impact

- **Application Layer**: Adds pure synchronous `def get_clinic_date_range_bounds(fecha_desde: datetime.date | None = None, fecha_hasta: datetime.date | None = None, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (**Hard Rule #3**).
- **Infrastructure Repository Layer**: Updates `SqlAlchemyTurnoRepository.find_by_patient_range` in `backend/app/infrastructure/repositories/turno.py` to chain `.options(selectinload(Turno.odontologo))` (**Hard Rule #2**).
- **API Layer**: Extends `backend/app/api/mis_turnos.py` with `OdontologoResumenResponse` and `MisTurnosPacienteItemResponse` (`ConfigDict(extra="forbid", from_attributes=True)`, **Hard Rule #1**) and role-dispatched `GET /api/mis-turnos`.
- **Tests**: Updates `backend/tests/test_dentist_agenda.py` (where `paciente` calling `?fecha=...` now expects `422` for dentist-only query parameter while `recepcion` still receives `403`) and adds `backend/tests/test_patient_portal.py` testing patient listing, optional range bounds, BOLA cross-patient isolation, E2E cancellation via `PATCH /api/turnos/{id}`, and `401`/`403`/`422` validations against real in-memory SQLite (**Hard Rule #7**) with synthetic data (**Hard Rule #12**).
