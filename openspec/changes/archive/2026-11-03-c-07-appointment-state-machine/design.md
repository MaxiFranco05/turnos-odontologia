# Design: C-07 — Appointment State Machine & Role Transitions (`c-07-appointment-state-machine`)

## Context

`C-02` (`core-models`) defined `EstadoTurno` (`solicitado`, `confirmado`, `anulado`, `cancelado`, `presente`, `ausente`) and `Turno` in `backend/app/domain/models/turno.py`. `C-03` and `C-04` established `get_current_user` and `require_roles(*allowed_roles)` in `backend/app/api/deps.py`. `C-05` (`availability-engine`) and `C-06` (`appointment-request`) already treat `EstadoTurno.CANCELADO` and `EstadoTurno.ANULADO` as non-blocking states (`CB-03`) in `calculate_free_slots` and `find_overlapping_for_update`.

See `proposal.md` for motivation and scope, and `specs/appointment-state-machine/spec.md` for normative requirements and scenarios.

## Goals / Non-Goals

**Goals:**
- Expose `PATCH /api/turnos/{id}` with a strict Pydantic v2 schema `TurnoEstadoUpdate` (`ConfigDict(extra="forbid")`) to perform partial state updates in strict compliance with **Hard Rule #8 (`NUNCA verbos en paths`)** and **Hard Rule #9 (`PATCH` for partial updates)**.
- Implement the state machine and anticipation rules as a pure synchronous function `def validate_state_transition(...)` in `backend/app/application/turnos.py` (**Hard Rule #3**: zero async I/O, zero infrastructure imports).
- Enforce strict separation between **authorization/ownership errors (`403 Forbidden`)**, **invalid state machine transitions (`409 Conflict`)**, and **temporal/anticipation window violations (`422 Unprocessable Entity`)**.
- Acquire a row-level lock (`select(Turno).where(Turno.id == id).with_for_update()`, **Hard Rule #2**) when loading the target appointment in `PATCH /api/turnos/{id}` to serialize concurrent state transitions on the same appointment.

**Non-Goals:**
- Exposing verb-based sub-routes (`/confirmar`, `/anular`, `/cancelar`, `/marcar-presente`, `/marcar-ausente`) — explicitly replaced by `PATCH /api/turnos/{id}` with `{"estado": "..."}` per user architectural confirmation and Hard Rules #8 and #9.
- Modifying fields other than `estado` on `Turno` (appointment rescheduling belongs to post-MVP v2 per `DD-05`).
- Role-specific agenda listing endpoints (`GET /api/agenda/dia`, `GET /api/mis-turnos`) — scoped to `C-08`, `C-09`, and `C-10`.

## Decisions

### 1. Resource-Oriented `PATCH /api/turnos/{id}` Replacing Verb Subpaths
- **Decision**: Implement a single `PATCH /api/turnos/{id}` endpoint in `backend/app/api/turnos.py` accepting `TurnoEstadoUpdate`:
  ```python
  class TurnoEstadoUpdate(BaseModel):
      model_config = ConfigDict(extra="forbid")

      estado: EstadoTurno
  ```
- **Rationale**: `CHANGES.md` originally drafted 5 verb sub-routes (`PATCH /api/turnos/{id}/confirmar`, etc.), which directly violate **Hard Rule #8 (`API/REST: NUNCA verbos en paths → URIs basadas en sustantivos`)** and **Hard Rule #9 (`PATCH` for partial resource updates)**. Following the exact precedent established in `C-05` (where `PUT /api/plantillas/{id}` was corrected to `PATCH /api/plantillas/{id}`), `PATCH /api/turnos/{id}` updates the `estado` attribute of the `Turno` resource via JSON Merge Patch semantics and updates `CHANGES.md` accordingly.

### 2. Pure Synchronous State-Machine Validator (`def validate_state_transition`)
- **Decision**: Implement `def validate_state_transition(...) -> None` in `backend/app/application/turnos.py` raising typed domain exceptions mapped deterministically at the HTTP boundary:
  - `UnauthorizedTransitionError` → HTTP `403 Forbidden`
  - `InvalidStateTransitionError` → HTTP `409 Conflict`
  - `AnticipationWindowError` → HTTP `422 Unprocessable Entity`
- **Evaluation Order (Defense in Depth)**:
  1. **Role-to-Target-State Allowlist (`RN-TU-01..04`, `RN-GL-01`)**:
     - `RolUsuario.PACIENTE` → `{EstadoTurno.CANCELADO}`
     - `RolUsuario.RECEPCION` → `{EstadoTurno.CONFIRMADO, EstadoTurno.ANULADO}`
     - `RolUsuario.ODONTOLOGO` → `{EstadoTurno.PRESENTE, EstadoTurno.AUSENTE}`
     - If `nuevo_estado` is not in the actor's allowed target set → raise `UnauthorizedTransitionError` (`403 Forbidden`).
  2. **Resource Ownership Check (`RN-AU-02`, `RN-GL-01`, OWASP API1:2023 BOLA)**:
     - If `actor_rol == RolUsuario.PACIENTE` and `turno_paciente_id != actor_user_id` → raise `UnauthorizedTransitionError` (`403 Forbidden`).
     - If `actor_rol == RolUsuario.ODONTOLOGO` and `turno_odontologo_id != actor_user_id` → raise `UnauthorizedTransitionError` (`403 Forbidden`).
     - (`RolUsuario.RECEPCION` has clinic-wide scope per `03_actores_y_roles.md`).
  3. **Source-to-Target State Machine Matrix (`DD-03`, `US-004`, `US-006`, `US-008`)**:
     - Target `EstadoTurno.CONFIRMADO` (by `recepcion`): valid source states = `{EstadoTurno.SOLICITADO}`.
     - Target `EstadoTurno.CANCELADO` (by `paciente`): valid source states = `{EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO}`.
     - Target `EstadoTurno.ANULADO` (by `recepcion`): valid source states = `{EstadoTurno.SOLICITADO, EstadoTurno.CONFIRMADO}`.
     - Target `EstadoTurno.PRESENTE` / `EstadoTurno.AUSENTE` (by `odontologo`): valid source states = `{EstadoTurno.CONFIRMADO}`.
     - If `estado_actual` is not in the valid source states for `nuevo_estado` → raise `InvalidStateTransitionError` (`409 Conflict`).
  4. **Temporal & Minimum Anticipation Rules (`RN-TU-05`, `RN-GL-02`)**:
     - Normalize `turno_inicio` and `now` to `ZoneInfo(timezone_str)` (`America/Argentina/Buenos_Aires`).
     - If `nuevo_estado in {EstadoTurno.CANCELADO, EstadoTurno.ANULADO}`:
       - Require `turno_inicio_local - now_local >= datetime.timedelta(hours=cancel_min_hours)` (default `24`). If `< timedelta(hours=cancel_min_hours)`, raise `AnticipationWindowError` (`422 Unprocessable Entity`).
     - If `nuevo_estado == EstadoTurno.CONFIRMADO`:
       - Require `turno_inicio_local > now_local` (`RN-GL-02`: cannot confirm an appointment in the past). If `<= now_local`, raise `AnticipationWindowError` (`422 Unprocessable Entity`).
- **Rationale**: Checking Role and Ownership **before** checking current state or anticipation prevents leaking appointment state details to unauthorized users (OWASP API1:2023). Checking State Matrix (`409`) before Anticipation (`422`) ensures that trying to cancel an already `cancelado` or `presente` appointment always reports the terminal-state conflict (`409`).

### 3. Transactional Row Locking on `PATCH /api/turnos/{id}`
- **Decision**: Load the appointment using `select(Turno).where(Turno.id == id).with_for_update()` (via `SqlAlchemyTurnoRepository.get_by_id_for_update(id)`).
- **Rationale**: If Reception attempts to confirm an appointment at the exact same millisecond the Patient cancels it, `FOR UPDATE` serializes the two transactions in PostgreSQL so the second transaction sees the updated `estado` after the first commits.

## Risks / Trade-offs

- **[Risk] Naive datetime hydrated by SQLite when comparing `turno.inicio - now_local`** → **Mitigation**: Reuse `_normalize_dt(turno.inicio, zone)` in `validate_state_transition` so naive timestamps from SQLite are normalized to `America/Argentina/Buenos_Aires` before subtracting `now_local`.
- **[Trade-off] Allowing `cancelado` and `anulado` from both `solicitado` and `confirmado`** → **Mitigation**: Matches real clinical workflow (`US-004`, `Flujo 5` and `Flujo 3`) where a patient or receptionist must be able to cancel/annul an already confirmed appointment as long as the 24-hour anticipation rule (`RN-TU-05`) is respected.
