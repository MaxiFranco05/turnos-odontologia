# Tasks: C-08 — Reception Daily Agenda (`c-08-reception-agenda`)

## 1. Repository Layer & Data Access

- [x] 1.1 Add `find_daily_agenda(start: datetime.datetime, end: datetime.datetime, odontologo_id: int | None = None) -> list[Turno]` to `TurnoRepository` interface (`backend/app/domain/repositories/turno.py`) and implement in `SqlAlchemyTurnoRepository` (`backend/app/infrastructure/repositories/turno.py`) using SQLAlchemy 2.0 `select()`, eager loading with `options(selectinload(Turno.paciente), selectinload(Turno.odontologo))`, and ordering by `Turno.inicio, Turno.id`. Verify by running `pytest backend/tests/test_turno_repository.py`.

## 2. API Schemas & Endpoint Implementation

- [x] 2.1 Define Pydantic v2 response projection schemas (`AgendaPacienteResponse`, `AgendaOdontologoResponse`, `AgendaTurnoDiaResponse`) in `backend/app/api/agenda.py` with `model_config = ConfigDict(extra="forbid", from_attributes=True)`, projecting only safe contact information (`nombre`, `nro_socio`, `email`) and strictly omitting `password_hash` and `debe_cambiar_password`. Verify schema validation behavior with extra field rejection.
- [x] 2.2 Implement `GET /api/agenda/dia` in `backend/app/api/agenda.py` protected by `Depends(require_roles(RolUsuario.RECEPCION))`, accepting required `fecha: date` and optional `odontologo_id: int`, computing clinic day bounds via `get_clinic_day_bounds`, performing `CB-06` dentist validation (404 if nonexistent, 422 if not an odontologist), and register the router under `/api/agenda` in `backend/app/main.py`. Verify by inspecting registered route list on FastAPI application instance.

## 3. Automated Tests & Acceptance Verification

- [x] 3.1 Create test suite `backend/tests/test_reception_agenda.py` using Testcontainers / test SQLite database without mocks (Hard Rule #7), synthetic patient/dentist fixtures (Hard Rule #12), covering all 9 spec scenarios: full day retrieval, filtering by dentist, RBAC 403 for `paciente` and `odontologo`, missing date 422, nonexistent dentist 404 (`CB-06`), non-dentist user 422 (`CB-06`), inclusion of `cancelado` with `origen=online` (`US-005 CA-1/CA-2`), empty day 200 `[]`, and BOPLA credential protection (absence of `password_hash`). Verify by running `pytest backend/tests/test_reception_agenda.py` and checking full test passage.

## Workflow follow-up

- Run `openspec validate --strict` to verify all change artifacts.
- Execute subagent audit with `dental-agenda-auditor`.
- Archive change upon task completion with `/opsx:archive c-08-reception-agenda`.
