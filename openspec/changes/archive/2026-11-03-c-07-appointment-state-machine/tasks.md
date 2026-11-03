# Tasks: C-07 — Appointment State Machine & Role Transitions (`c-07-appointment-state-machine`)

## 1. Repository Layer (`TurnoRepository` & `SqlAlchemyTurnoRepository`)

- [x] 1.1 Extend `TurnoRepository` (`backend/app/domain/repositories/turno.py`) and `SqlAlchemyTurnoRepository` (`backend/app/infrastructure/repositories/turno.py`) with `get_by_id_for_update(id: int) -> Turno | None` using SQLAlchemy 2.0 `select(Turno).where(Turno.id == id).with_for_update()` (**Hard Rule #2**).
  - **Strict TDD (`backend/tests/test_appointment_state_machine.py`)**:
    - **RED**: Write repository integration tests against real in-memory SQLite (`sqlite+aiosqlite:///:memory:`, **Hard Rule #7**) verifying:
      1. `get_by_id_for_update` returns the persisted `Turno` when the ID exists.
      2. `get_by_id_for_update` returns `None` when the ID does not exist.
    - **GREEN**: Implement `get_by_id_for_update` in `TurnoRepository` and `SqlAlchemyTurnoRepository` using `select(Turno).where(Turno.id == id).with_for_update()`.
    - **TRIANGULATE & REFACTOR**: Verify multiple synthetic appointments (**Hard Rule #12**) and confirm zero legacy `Session.query()` calls (**Hard Rule #2**).

## 2. Pure Domain State Machine & Anticipation Validator (`application/turnos.py`)

- [x] 2.1 Implement domain exceptions (`UnauthorizedTransitionError`, `InvalidStateTransitionError`, `AnticipationWindowError`) and pure synchronous `def validate_state_transition(...) -> None` in `backend/app/application/turnos.py` (**Hard Rule #3**: synchronous `def`, zero I/O, zero `infrastructure` imports).
  - **Strict TDD (`backend/tests/test_appointment_state_machine.py`)**:
    - **RED**: Write unit tests for `validate_state_transition` covering:
      1. **Role Allowlist (`RN-TU-01..04`, `RN-GL-01`)**:
         - `paciente` attempting `confirmado`, `anulado`, `presente`, or `ausente` raises `UnauthorizedTransitionError`.
         - `recepcion` attempting `cancelado`, `presente`, or `ausente` raises `UnauthorizedTransitionError`.
         - `odontologo` attempting `confirmado`, `anulado`, or `cancelado` raises `UnauthorizedTransitionError`.
      2. **Resource Ownership (`RN-AU-02`, `RN-GL-01`, OWASP BOLA)**:
         - `paciente` attempting `cancelado` when `turno_paciente_id != actor_user_id` raises `UnauthorizedTransitionError` even before checking current state or anticipation.
         - `odontologo` attempting `presente` or `ausente` when `turno_odontologo_id != actor_user_id` raises `UnauthorizedTransitionError` even before checking current state.
         - `recepcion` is allowed across any `turno_paciente_id` / `turno_odontologo_id`.
      3. **State Transition Matrix (`DD-03`, `US-004`, `US-006`, `US-008`)**:
         - Valid transitions pass:
           - `recepcion`: `solicitado -> confirmado` (future appointment), `solicitado -> anulado` (`>= 24h`), `confirmado -> anulado` (`>= 24h`).
           - `paciente` (owner): `solicitado -> cancelado` (`>= 24h`), `confirmado -> cancelado` (`>= 24h`).
           - `odontologo` (assigned): `confirmado -> presente`, `confirmado -> ausente`.
         - Invalid source states raise `InvalidStateTransitionError`:
           - `recepcion` attempting `confirmado -> confirmado`, `cancelado -> confirmado`, `anulado -> anulado`, `presente -> anulado`, `ausente -> anulado`.
           - `paciente` (owner) attempting `cancelado -> cancelado`, `anulado -> cancelado`, `presente -> cancelado`, `ausente -> cancelado`.
           - `odontologo` (assigned) attempting `solicitado -> presente`, `solicitado -> ausente`, `cancelado -> presente`, `anulado -> ausente`, `presente -> ausente`, `ausente -> presente`.
      4. **Minimum Anticipation & Temporal Rules (`RN-TU-05`, `RN-GL-02`, `CANCEL_MIN_HOURS=24`)**:
         - `cancelado` or `anulado` at `23h 59m 59s` before `turno_inicio` raises `AnticipationWindowError`.
         - `cancelado` or `anulado` at exactly `24h 00m 00s` (`turno_inicio - now == timedelta(hours=24)`) passes.
         - `confirmado` when `turno_inicio <= now` raises `AnticipationWindowError`.
         - Naive `datetime` from SQLite vs aware `datetime` normalization in `America/Argentina/Buenos_Aires` passes without `TypeError`.
    - **GREEN**: Implement `UnauthorizedTransitionError`, `InvalidStateTransitionError`, `AnticipationWindowError`, and `def validate_state_transition(...)` in `backend/app/application/turnos.py`.
    - **TRIANGULATE & REFACTOR**: Verify `inspect.iscoroutinefunction(validate_state_transition)` is `False` (**Hard Rule #3**).

## 3. REST Endpoint `PATCH /api/turnos/{id}` & Integration Tests (`api/turnos.py`)

- [x] 3.1 Implement `TurnoEstadoUpdate` (`ConfigDict(extra="forbid")`, **Hard Rule #1**) and `PATCH /api/turnos/{id}` (**Hard Rules #8 and #9**) in `backend/app/api/turnos.py`, protected by `Depends(require_roles(RolUsuario.PACIENTE, RolUsuario.RECEPCION, RolUsuario.ODONTOLOGO))`.
  - **Strict TDD (`backend/tests/test_appointment_state_machine.py`)**:
    - **RED**: Write HTTP integration tests via `AsyncClient` against real in-memory SQLite (**Hard Rule #7**) with synthetic clinical data (**Hard Rule #12**) covering:
      1. `200 OK`: `recepcion` confirms a `solicitado` appointment (`PATCH /api/turnos/{id}` with `{"estado": "confirmado"}`).
      2. `200 OK`: `paciente` cancels own `solicitado` and `confirmado` appointments with `>= 24h` anticipation (`{"estado": "cancelado"}`), and verify `GET /api/disponibilidad` and `POST /api/turnos` immediately treat the slot as free (`CB-03`).
      3. `200 OK`: `recepcion` annuls `solicitado` and `confirmado` appointments with `>= 24h` anticipation (`{"estado": "anulado"}`), and verify `GET /api/disponibilidad` and `POST /api/turnos` immediately treat the slot as free (`CB-03`).
      4. `200 OK`: `odontologo` marks own `confirmado` appointments as `presente` and `ausente`.
      5. `422 Unprocessable Entity`: `paciente` cancelling or `recepcion` annulling with `< 24h` anticipation (`23h` remaining) is rejected and DB state remains unchanged.
      6. `422 Unprocessable Entity`: `recepcion` attempting to confirm a past `solicitado` appointment is rejected (`RN-GL-02`).
      7. `422 Unprocessable Entity`: Undeclared extra fields in payload (`{"estado": "cancelado", "paciente_id": 999}`) or invalid enum value (`{"estado": "eliminado"}`) are rejected (**Hard Rule #1**).
      8. `403 Forbidden`: Role violations (`paciente` -> `confirmado`/`anulado`/`presente`/`ausente`; `recepcion` -> `cancelado`/`presente`/`ausente`; `odontologo` -> `confirmado`/`anulado`/`cancelado`).
      9. `403 Forbidden` (OWASP BOLA): `paciente` B attempting to cancel `paciente` A's appointment; `odontologo` B attempting to mark `odontologo` A's appointment `presente`/`ausente`.
      10. `403 Forbidden`: User with `debe_cambiar_password=True` receives `"password_change_required"`.
      11. `401 Unauthorized`: Unauthenticated request without Bearer token.
      12. `409 Conflict`: Invalid source state transitions (`odontologo` marking `solicitado -> presente/ausente`; `paciente` cancelling already `cancelado`/`presente` appointment; `recepcion` annulling already `anulado`/`presente` appointment).
      13. `404 Not Found`: `PATCH /api/turnos/999999` on non-existent ID.
    - **GREEN**: Implement `TurnoEstadoUpdate` and `PATCH /api/turnos/{id}` in `backend/app/api/turnos.py`.
    - **TRIANGULATE & REFACTOR**: Run full test suite (`pytest -q`) to confirm all existing and new tests pass with zero regressions.
