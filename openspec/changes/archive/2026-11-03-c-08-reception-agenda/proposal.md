# Proposal: C-08 — Reception Daily Agenda (`c-08-reception-agenda`)

## Why

Receptionists coordinate the entire clinic's daily workflow, patient arrivals, and dentist schedules. To validate appointments, confirm pending requests (`US-006`), and track patient attendance, reception requires a dedicated, unified daily agenda endpoint showing all appointments across all dentists for a given calendar date, with optional dentist filtering, while enforcing strict role-based access control and preventing unauthorized data leakage.

## What Changes

- Add a new Reception-only REST endpoint `GET /api/agenda/dia` (with query parameter `fecha: YYYY-MM-DD` and optional `odontologo_id: int`) to query all appointments for a specific calendar date in clinic timezone (`America/Argentina/Buenos_Aires`).
- Enforce strict server-side RBAC: restricted exclusively to `RolUsuario.RECEPCION` (`403 Forbidden` for `paciente` and `odontologo`, enforcing `RN-GL-01` and `RN-AU-02`).
- Include appointments in all lifecycle states (`solicitado`, `confirmado`, `cancelado`, `anulado`, `presente`, `ausente`), explicitly preserving patient-reported cancellations (`cancelado`) and online booking origin (`origen=online`) to fulfill `US-005 CA-1` and `CA-2`.
- Eagerly load both `Turno.paciente` and `Turno.odontologo` relationships using SQLAlchemy 2.0 `selectinload` to completely prevent N+1 query overhead.
- Protect patient and dentist privacy (OWASP API3:2023 BOPLA and Hard Rule #1): define strict Pydantic schemas with `model_config = ConfigDict(extra="forbid")` projecting only required contact/identification fields (`id`, `nombre`, `nro_socio`, `email`), never exposing sensitive attributes like `password_hash` or `debe_cambiar_password`.
- Validate optional `odontologo_id` against the database (`CB-06`): return `404 Not Found` if the user ID does not exist, and `422 Unprocessable Entity` if the user exists but does not have `rol == RolUsuario.ODONTOLOGO`.
- Order results deterministically by appointment start time (`Turno.inicio`) ascending, then by `Turno.id`.

## Capabilities

### New Capabilities
- `reception-agenda`: Daily clinic-wide appointment agenda view with dentist filtering, eager loading of participant details, and state tracking for receptionists.

### Modified Capabilities
None.

## Impact

- **API Layer**: New router `backend/app/api/agenda.py` mounted at prefix `/api/agenda`, registered in `backend/app/main.py`.
- **Domain & Repository Layer**: Add `find_daily_agenda(start: datetime.datetime, end: datetime.datetime, odontologo_id: int | None = None) -> list[Turno]` to `TurnoRepository` protocol (`backend/app/domain/repositories/turno.py`) and implement in `SqlAlchemyTurnoRepository` (`backend/app/infrastructure/repositories/turno.py`).
- **Application Layer**: Reuse `get_clinic_day_bounds(fecha, timezone_str)` from `backend/app/application/turnos.py` to calculate exact timezone-aware day bounds.
- **Testing**: New comprehensive test suite `backend/tests/test_reception_agenda.py` validating happy path, filtering, RBAC restrictions, missing/invalid dentist handling, and zero credential leakage against a real database without mocks.
