# Tasks: C-06 — Appointment Request & Transactional Anti-Overlap (`c-06-appointment-request`)

## 1. Repository Layer — Transactional Overlap Locking (`SELECT ... FOR UPDATE`)

- [x] 1.1 [TDD RED→GREEN→REFACTOR] Extend `TurnoRepository` (`backend/app/domain/repositories/turno.py`) and `SqlAlchemyTurnoRepository` (`backend/app/infrastructure/repositories/turno.py`) with `find_overlapping_for_update(odontologo_id: int, inicio: datetime.datetime, fin: datetime.datetime, exclude_turno_id: int | None = None) -> list[Turno]` using SQLAlchemy 2.0 `select(Turno).where(...).with_for_update()` (Hard Rule #2). Verify with real in-memory SQLite tests (zero mocks, Hard Rule #7; synthetic data, Hard Rule #12) in `backend/tests/test_appointment_request.py` covering:
  - Active appointments (`solicitado`, `confirmado`, `presente`, `ausente`) intersecting `[inicio, fin)` are returned (`RN-AG-01`, `CB-04`).
  - Appointments in state `cancelado` or `anulado` are excluded and do not block the interval (`CB-03`, `RN-TU-04`).
  - Contiguous adjacent intervals (`fin_A == inicio_B`, `CB-01`) return an empty list without false overlap.

## 2. Application Layer — Pure Synchronous Template-Slot & Timezone Validator

- [x] 2.1 [TDD RED→GREEN→REFACTOR] Implement pure synchronous helper `def validate_slot_matches_template(inicio: datetime.datetime, fin: datetime.datetime, templates: list[PlantillaDisponibilidad], timezone_str: str | None = None, now_override: datetime.datetime | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (strictly `def`, not `async def`, per Hard Rule #3). Verify with unit tests in `backend/tests/test_appointment_request.py` covering:
  - Normalizes `inicio` and `fin` into `ZoneInfo(timezone_str)` (`America/Argentina/Buenos_Aires`) and returns the normalized `(inicio_local, fin_local)` tuple when `[inicio, fin)` matches an exact grid slot of `duracion_slot_minutos` (`RN-AG-02`).
  - Rejects past dates (`inicio.date() < now_local.date()`) and already elapsed same-day slots (`inicio_local <= now_local`) (`RN-GL-02`, `CB-05`).
  - Rejects intervals outside any template for `inicio.date().weekday()`, intervals with duration different from `duracion_slot_minutos`, misaligned start times (`09:10–09:40`), or incomplete trailing remainders (`09:40–10:00` on a `09:00–10:00` template with `40 min` slots, `CB-02`).

## 3. API Layer — Strict Pydantic v2 Schemas & Patient RBAC Boundary (`POST /api/turnos`)

- [x] 3.1 [TDD RED→GREEN→REFACTOR] Create `TurnoCreate` and `TurnoResponse` schemas in `backend/app/api/turnos.py` with `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)` (Hard Rule #1), validating `odontologo_id > 0`, `motivo` (`min_length=1, max_length=255`), and `@model_validator(mode="after")` enforcing `fin > inicio`. Verify via tests in `backend/tests/test_appointment_request.py` that undeclared fields (`{"paciente_id": 99, "estado": "confirmado", "box": 1}`), whitespace-only `motivo` (`"   "`), and `fin <= inicio` are rejected with HTTP `422 Unprocessable Entity`.
- [x] 3.2 [TDD RED→GREEN→REFACTOR] Implement `POST /api/turnos` in `backend/app/api/turnos.py` (Hard Rule #8 noun-based URI) protected by `Depends(require_roles(RolUsuario.PACIENTE))` and register `turnos_router` in `backend/app/main.py`. Orchestrate dentist existence/role validation (`CB-06`), template-slot validation (`validate_slot_matches_template`), transactional overlap check (`find_overlapping_for_update` + `IntegrityError` rollback handler → `409 Conflict`), and creation with `paciente_id=current_user.id`, `estado=EstadoTurno.SOLICITADO`, and `origen=OrigenTurno.ONLINE`. Verify with real SQLite integration tests in `backend/tests/test_appointment_request.py` covering:
  - Expected behavior (`201 Created`): valid patient request on a free template slot creates a `Turno` with `estado="solicitado"`, `origen="online"`, `paciente_id=current_user.id`, and subsequent `GET /api/disponibilidad` no longer lists that slot as free (`US-003 CA-1..CA-3`).
  - RBAC & Auth errors (`401`/`403`): unauthenticated requests return `401 Unauthorized`; users with role `recepcion` or `odontologo` return `403 Forbidden` (`RN-TU-01`, `RN-GL-01`); patients with `debe_cambiar_password=True` return `403 Forbidden` (`"password_change_required"`, `US-010`).
  - Dentist validation errors (`CB-06`): non-existent `odontologo_id` returns `404 Not Found`; `odontologo_id` belonging to a `paciente` or `recepcion` user returns `422 Unprocessable Entity`.
  - Schedule & timezone errors (`422 Unprocessable Entity`): slot outside template hours or on a weekday without templates (`RN-AG-02`), misaligned/incomplete remainder slot (`CB-02`), past date (`RN-GL-02`), and already elapsed slot on the current clinic day (`CB-05`).
  - Anti-overlap & concurrency invariants (`409 Conflict` vs `201 Created`): overlapping an existing `solicitado`, `confirmado`, `presente`, or `ausente` appointment returns `409 Conflict` (`RN-AG-01`, `CB-04`, Hard Rule #13); booking a slot whose previous appointment is `cancelado` or `anulado` succeeds with `201 Created` (`CB-03`, `RN-TU-04`); booking a contiguous adjacent slot (`09:00–09:30` followed by `09:30–10:00`, `CB-01`) succeeds with `201 Created`.

## Workflow follow-up

- Run full backend test suite (`pytest`) and linters (`ruff`, `mypy`) after implementation in `/opsx:apply`.
- Archive the change via `/opsx:archive c-06-appointment-request` and mark `[x]` in `CHANGES.md` once all tasks and tests pass.
