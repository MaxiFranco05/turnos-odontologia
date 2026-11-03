# Tasks: C-09 — Dentist Daily Agenda (`c-09-dentist-agenda`)

## 1. Pure Clinic-Day Window Calculation (`application/turnos.py`)

- [x] 1.1 Implement pure synchronous `def get_clinic_day_bounds(fecha: datetime.date, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (**Hard Rule #3**: synchronous `def`, zero I/O, zero `infrastructure` imports).
  - **Strict TDD (`backend/tests/test_dentist_agenda.py`)**:
    - **RED**: Write unit tests verifying:
      1. `inspect.isfunction(get_clinic_day_bounds)` is `True` and `inspect.iscoroutinefunction(get_clinic_day_bounds)` is `False` (**Hard Rule #3**).
      2. Given `fecha=datetime.date(2027, 6, 7)`, returns `day_start = 2027-06-07 00:00:00-03:00` and `day_end = 2027-06-08 00:00:00-03:00` (`day_end - day_start == timedelta(days=1)`) in `America/Argentina/Buenos_Aires`.
    - **GREEN**: Implement `def get_clinic_day_bounds(...)` in `backend/app/application/turnos.py`.
    - **TRIANGULATE & REFACTOR**: Verify across multiple dates (including leap/month boundaries) and confirm zero `infrastructure` imports in `backend/app/application/turnos.py`.

## 2. Strict Response DTOs & `GET /api/mis-turnos` Endpoint (`api/mis_turnos.py` & `main.py`)

- [x] 2.1 Implement `PacienteResumenResponse` and `MisTurnosOdontologoItemResponse` (`ConfigDict(extra="forbid", from_attributes=True)`, **Hard Rule #1**) and `GET /api/mis-turnos?fecha=YYYY-MM-DD` (**Hard Rule #8**) in `backend/app/api/mis_turnos.py`, protected by `Depends(require_roles(RolUsuario.ODONTOLOGO))`, and register `mis_turnos_router` in `backend/app/main.py`.
  - **Strict TDD (`backend/tests/test_dentist_agenda.py`)**:
    - **RED**: Write unit and HTTP integration tests against real in-memory SQLite (`sqlite+aiosqlite:///:memory:`, **Hard Rule #7**) with 100% synthetic clinical data (**Hard Rule #12**) verifying:
      1. Schema strictness (**Hard Rule #1**, OWASP API3:2023 BOPLA): `PacienteResumenResponse` and `MisTurnosOdontologoItemResponse` reject undeclared extra fields (`ValidationError`) and never expose `password_hash`, `debe_cambiar_password`, or `rol`.
      2. `200 OK` (Expected Behavior — `US-007 CA-1`, `Flujo 4`): Authenticated `odontologo` Dra. Sofía Martín receives her appointments on `2027-06-07` across all 6 states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`), ordered ascending by `inicio`, including contiguous `09:00–09:30` and `09:30–10:00` intervals (`CB-01`), with nested `paciente` (`id`, `nombre`, `nro_socio`, `email`).
      3. `200 OK` (OWASP API1:2023 BOLA / Multi-Dentist Isolation — `US-007 CA-1`, `RN-AU-02`): Appointments belonging to synthetic dentist Dr. Juan Pérez on the same date (`2027-06-07`) are strictly excluded when Dra. Sofía Martín queries `GET /api/mis-turnos?fecha=2027-06-07`, and vice versa.
      4. `200 OK` (Date Window Isolation & Empty Day): Appointments from `2027-06-06` or `2027-06-08` are excluded when querying `2027-06-07`; querying a date with no appointments (`2027-06-09`) returns `[]`.
      5. `401 Unauthorized`: Unauthenticated request without Bearer token is rejected.
      6. `403 Forbidden` (`RN-GL-01`, `US-010`): Requests authenticated as `paciente` or `recepcion`, or as an `odontologo` with `debe_cambiar_password=True` (`"password_change_required"`), are rejected with `403`.
      7. `422 Unprocessable Entity`: Missing `fecha` (`GET /api/mis-turnos`) or invalid `fecha` (`GET /api/mis-turnos?fecha=no-es-fecha`) is rejected with `422`.
    - **GREEN**: Create `backend/app/api/mis_turnos.py`, wire `app.include_router(mis_turnos_router)` in `backend/app/main.py`, and run `pytest tests/test_dentist_agenda.py -q`.
    - **TRIANGULATE & REFACTOR**: Run full test suite (`pytest -q`) to confirm zero regressions across all existing tests.
