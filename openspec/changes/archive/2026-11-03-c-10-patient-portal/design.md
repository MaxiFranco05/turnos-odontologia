# Design: C-10 — Patient Portal Self-Appointments (`c-10-patient-portal`)

## Context

`C-09` (`dentist-agenda`) introduced `backend/app/api/mis_turnos.py` with `GET /api/mis-turnos` for `RolUsuario.ODONTOLOGO`. `C-02` (`core-models`) already defined `SqlAlchemyTurnoRepository.find_by_patient_range(paciente_id, start, end)` in `backend/app/infrastructure/repositories/turno.py`, and `C-07` (`appointment-state-machine`) implemented patient cancellation (`PATCH /api/turnos/{id}` with `{"estado": "cancelado"}` and 24-hour minimum anticipation).

See `proposal.md` for motivation and scope, and `specs/patient-portal/spec.md` and `specs/dentist-agenda/spec.md` for normative requirements and scenarios.

## Goals / Non-Goals

**Goals:**
- Extend `GET /api/mis-turnos` in `backend/app/api/mis_turnos.py` to support `RolUsuario.PACIENTE` alongside `RolUsuario.ODONTOLOGO` via `Depends(require_roles(RolUsuario.ODONTOLOGO, RolUsuario.PACIENTE))`.
- Enforce strict server-side BOLA isolation (`paciente_id = current_user.id` extracted exclusively from the JWT token, never from query parameters).
- Provide a pure synchronous function `def get_clinic_date_range_bounds(fecha_desde: datetime.date | None = None, fecha_hasta: datetime.date | None = None, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (**Hard Rule #3**: synchronous `def`, zero I/O, zero `infrastructure` imports).
- Prevent N+1 queries by chaining `.options(selectinload(Turno.odontologo))` in `SqlAlchemyTurnoRepository.find_by_patient_range` (**Hard Rule #2**).
- Define strict Pydantic v2 response schemas `OdontologoResumenResponse` and `MisTurnosPacienteItemResponse` with `ConfigDict(extra="forbid", from_attributes=True)` (**Hard Rule #1**, OWASP API3:2023 BOPLA).

**Non-Goals:**
- Re-implementing `PATCH /api/turnos/{id}` — already implemented and audited in `C-07`, and verified end-to-end with `GET /api/mis-turnos` in `backend/tests/test_patient_portal.py`.
- Reception clinic-wide daily agenda (`GET /api/agenda/dia`) — scoped to `C-08`.

## Decisions

### 1. Pure Synchronous Date-Range Bounds Calculation (`def get_clinic_date_range_bounds`)
- **Decision**: Implement `def get_clinic_date_range_bounds(...)` in `backend/app/application/turnos.py`:
  - Validates that if both `fecha_desde` and `fecha_hasta` are provided, `fecha_hasta >= fecha_desde`; otherwise raises `ValueError`.
  - Defaults `start_date = fecha_desde or datetime.date(1970, 1, 1)` and `end_date = fecha_hasta or datetime.date(2100, 1, 1)`.
  - Computes `range_start = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=zone)` (`00:00:00-03:00` on `start_date`) and `range_end = datetime.datetime.combine(end_date, datetime.time.min, tzinfo=zone) + datetime.timedelta(days=1)` (`00:00:00-03:00` on the day after `end_date`, making `fecha_hasta` inclusive for the entire clinic day).
- **Rationale**: Complies with **Hard Rule #3** (`def` synchronous without I/O or clock calls) and allows `SqlAlchemyTurnoRepository.find_by_patient_range(paciente_id=current_user.id, start=range_start, end=range_end)` to execute a single indexed range query (`ix_turnos_paciente_inicio`) whether the patient supplies 0, 1, or 2 date bounds.

### 2. Role-Based Parameter Contract on Unified `GET /api/mis-turnos`
- **Decision**: In `list_mis_turnos` (`backend/app/api/mis_turnos.py`):
  - If `current_user.rol == RolUsuario.ODONTOLOGO`:
    - Requires `fecha is not None` and forbids `fecha_desde` / `fecha_hasta` (raising `HTTPException(422)` if violated).
    - Returns `list[MisTurnosOdontologoItemResponse]` (each containing nested `paciente: PacienteResumenResponse`).
  - If `current_user.rol == RolUsuario.PACIENTE`:
    - Forbids dentist-only `fecha` parameter (raising `HTTPException(422)` if `fecha is not None`).
    - Accepts optional `fecha_desde` and `fecha_hasta`, validates range via `get_clinic_date_range_bounds`, and returns `list[MisTurnosPacienteItemResponse]` (each containing nested `odontologo: OdontologoResumenResponse`).
- **Rationale**: Keeps `/api/mis-turnos` as a single cohesive REST resource while enforcing unambiguous query parameter validation (`422`) and least-privilege response projection per role (`response_model=list[MisTurnosOdontologoItemResponse] | list[MisTurnosPacienteItemResponse]`).

### 3. Explicit `selectinload(Turno.odontologo)` in `find_by_patient_range`
- **Decision**: Chain `.options(selectinload(Turno.odontologo))` in `SqlAlchemyTurnoRepository.find_by_patient_range` (`backend/app/infrastructure/repositories/turno.py`).
- **Rationale**: Mirrors the N+1 prevention applied to `find_by_dentist_range` in `C-09`, guaranteeing that serializing `MisTurnosPacienteItemResponse.odontologo` always executes in at most 2 SQL statements (**Hard Rule #2**).

## Risks / Trade-offs

- **[Risk] Union response model `list[MisTurnosOdontologoItemResponse] | list[MisTurnosPacienteItemResponse]` in FastAPI** → **Mitigation**: Each handler branch explicitly constructs and returns `[MisTurnosOdontologoItemResponse.model_validate(t) ...]` or `[MisTurnosPacienteItemResponse.model_validate(t) ...]`, ensuring deterministic serialization and strict `extra="forbid"` enforcement before returning.
