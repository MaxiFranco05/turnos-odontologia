# Proposal: C-07 — Appointment State Machine & Role Transitions (`c-07-appointment-state-machine`)

## Why

With online appointment creation (`POST /api/turnos`) completed in `C-06`, every reservation starts in state `solicitado` (`US-003 CA-1`). However, the system still lacks the server-side state machine and REST endpoint to govern lifecycle transitions across the three clinical actors (`paciente`, `recepcion`, `odontologo`): patients cancelling their own appointments (`US-004`, `Flujo 5`), receptionists confirming or annulling appointments (`US-006`, `Flujo 3`), and dentists recording attendance (`presente` / `ausente`, `US-008`, `Flujo 4`). Without `C-07`, the role-specific agenda views (`C-08`, `C-09`, `C-10`) and frontend workflows (`C-13`, `C-14`, `C-15`) are blocked at **GATE 4 / GATE 5**.

## What Changes

- **Resource-Oriented Partial State Update (`PATCH /api/turnos/{id}`)**:
  - Exposes `PATCH /api/turnos/{id}` accepting a strict Pydantic v2 payload `TurnoEstadoUpdate` (`{"estado": EstadoTurno}`, `ConfigDict(extra="forbid")`), replacing the legacy verb subpaths (`/confirmar`, `/anular`, `/cancelar`, `/marcar-presente`, `/marcar-ausente`) listed in early `CHANGES.md` drafts to strictly comply with **Hard Rule #8 (`NUNCA verbos en paths`)** and **Hard Rule #9 (`PATCH` for partial resource updates)**.
  - Protected by `Depends(require_roles(RolUsuario.PACIENTE, RolUsuario.RECEPCION, RolUsuario.ODONTOLOGO))` (enforcing JWT authentication and `debe_cambiar_password == False` per `US-010`).
- **Pure Synchronous State-Machine & Anticipation Validator (`def validate_state_transition`)**:
  - Enforces the role-scoped transition matrix (`DD-03`, `RN-TU-01..04`, `RN-GL-01`, `RN-AU-02`):
    - **`RolUsuario.PACIENTE`**:
      - Allowed target state: `EstadoTurno.CANCELADO` only (`RN-TU-01`, `RN-TU-04`). Any other target state returns HTTP `403 Forbidden` (`RN-GL-01`).
      - Ownership invariant: `turno.paciente_id == current_user.id`; attempting to transition another patient's appointment returns HTTP `403 Forbidden` (OWASP API1:2023 BOLA/IDOR protection).
      - Allowed source states: `EstadoTurno.SOLICITADO` or `EstadoTurno.CONFIRMADO`. Any other source state (`cancelado`, `anulado`, `presente`, `ausente`) returns HTTP `409 Conflict`.
      - Minimum anticipation (`RN-TU-05`, `RN-GL-02`): Requires `turno.inicio - now_local >= timedelta(hours=settings.CANCEL_MIN_HOURS)` (default `24` hours in `America/Argentina/Buenos_Aires`), returning HTTP `422 Unprocessable Entity` if within `< 24h` or in the past.
    - **`RolUsuario.RECEPCION`**:
      - Allowed target states: `EstadoTurno.CONFIRMADO` or `EstadoTurno.ANULADO` (`RN-TU-02`, `RN-TU-04`). Any other target state (`cancelado`, `presente`, `ausente`, `solicitado`) returns HTTP `403 Forbidden` (`RN-GL-01`).
      - Ownership scope: All clinic appointments (`03_actores_y_roles.md`).
      - Allowed source states:
        - For `confirmado`: only `EstadoTurno.SOLICITADO` (and `turno.inicio > now_local` per `RN-GL-02`; if already `confirmado` or terminal, returns `409 Conflict`; if in the past, returns `422 Unprocessable Entity`).
        - For `anulado`: `EstadoTurno.SOLICITADO` or `EstadoTurno.CONFIRMADO` (any other source state returns `409 Conflict`).
      - Minimum anticipation for `anulado` (`RN-TU-05`): Requires `turno.inicio - now_local >= timedelta(hours=settings.CANCEL_MIN_HOURS)` (`24h`), returning HTTP `422 Unprocessable Entity` if violated.
    - **`RolUsuario.ODONTOLOGO`**:
      - Allowed target states: `EstadoTurno.PRESENTE` or `EstadoTurno.AUSENTE` (`RN-TU-03`). Any other target state returns HTTP `403 Forbidden` (`RN-GL-01`).
      - Ownership invariant (`RN-AU-02`, `RN-GL-01`): `turno.odontologo_id == current_user.id`; attempting to transition another dentist's appointment returns HTTP `403 Forbidden`.
      - Allowed source state: `EstadoTurno.CONFIRMADO` only (`US-008 CA-2`). Attempting to mark `presente`/`ausente` from `solicitado`, `cancelado`, `anulado`, `presente`, or `ausente` returns HTTP `409 Conflict`.
- **Slot Release Integration (`CB-03`, `RN-TU-04`)**:
  - Transitioning an appointment to `cancelado` (by patient) or `anulado` (by reception) immediately releases its `[inicio, fin)` interval in both `GET /api/disponibilidad` (`C-05`) and `POST /api/turnos` (`C-06`) while preserving in `turno.estado` which role executed the cancellation (`RN-TU-04`).

## Capabilities

### New Capabilities
- `appointment-state-machine`: Server-side appointment lifecycle state machine (`PATCH /api/turnos/{id}`) enforcing role-based transition permissions (`RN-TU-01..04`, `RN-GL-01`), resource ownership (`RN-AU-02`), and configurable minimum cancellation/annulment anticipation (`RN-TU-05`, `CANCEL_MIN_HOURS=24`).

### Modified Capabilities
<!-- No existing capability requirements are modified. -->

## Impact

- **Application Layer**: Extends `backend/app/application/turnos.py` with domain exceptions (`UnauthorizedTransitionError`, `InvalidStateTransitionError`, `AnticipationWindowError`) and the pure synchronous validator `def validate_state_transition(...)` (Hard Rule #3).
- **API Layer**: Extends `backend/app/api/turnos.py` with `TurnoEstadoUpdate` (`ConfigDict(extra="forbid")`, Hard Rule #1) and `PATCH /api/turnos/{id}` (Hard Rules #8 and #9) using row-level locking (`select(Turno).where(Turno.id == id).with_for_update()`, Hard Rule #2).
- **Roadmap Documentation**: Updates `CHANGES.md` (`C-07` and `C-10`) to reflect `PATCH /api/turnos/{id}` with `{"estado": "..."}` in place of legacy verb subpaths per Hard Rules #8 and #9.
- **Tests**: Adds `backend/tests/test_appointment_state_machine.py` testing the complete transition matrix, cross-user BOLA/ownership rejections (`403`), invalid state conflicts (`409`), 24-hour anticipation boundaries (`422`), and slot release (`CB-03`) against real in-memory SQLite (Hard Rule #7) with 100% synthetic data (Hard Rule #12).
