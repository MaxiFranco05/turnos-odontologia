# Tasks: C-05 — Availability Engine & Schedule Templates (`c-05-availability-engine`)

## 1. Repository Layer — Template Overlap Detection

- [ ] 1.1 Extend `PlantillaRepository` protocol (`backend/app/domain/repositories/plantilla.py`) and `SqlAlchemyPlantillaRepository` (`backend/app/infrastructure/repositories/plantilla.py`) with `find_overlapping_templates(odontologo_id: int, dia_semana: int, hora_inicio: datetime.time, hora_fin: datetime.time, exclude_id: int | None = None) -> list[PlantillaDisponibilidad]` using SQLAlchemy 2.0 `select()` (`hora_inicio < fin AND hora_fin > inicio`). Verify with real-DB tests in `backend/tests/test_availability_engine.py` covering overlapping intervals (rejected) and contiguous adjacent intervals `09:00–11:00` + `11:00–13:00` (`CB-01`, accepted).

## 2. Application Layer — Pure Synchronous Slot-Derivation Engine

- [ ] 2.1 Implement pure synchronous helper `def calculate_free_slots(...)` in `backend/app/application/availability.py` (following Hard Rule #3: `def`, not `async def`) that partitions `PlantillaDisponibilidad` windows by `duracion_slot_minutos` in `ZoneInfo(settings.TIMEZONE)`, discards trailing incomplete remainders (`CB-02`), filters out elapsed slots when `fecha == today` (`CB-05`, `RN-GL-02`), and subtracts active appointments (`solicitado`, `confirmado`, `presente`, `ausente`, `CB-04`) while keeping `cancelado` and `anulado` slots available (`CB-03`, `RN-TU-04`). Verify with unit/integration tests in `backend/tests/test_availability_engine.py` asserting exact slot boundaries for each scenario.

## 3. API Layer — Reception Template CRUD (`/api/plantillas`)

- [ ] 3.1 Create Pydantic v2 request/response schemas (`PlantillaCreate`, `PlantillaUpdate`, `PlantillaResponse`) in `backend/app/api/plantillas.py` with `model_config = ConfigDict(extra="forbid")` (Hard Rule #1), `dia_semana` bounds (`0..6`), `duracion_slot_minutos > 0`, and `@model_validator(mode="after")` enforcing `hora_fin > hora_inicio`. Verify via tests in `backend/tests/test_availability_engine.py` that undeclared fields (`{"box": 1}`) and inverted time ranges return HTTP `422 Unprocessable Entity`.
- [ ] 3.2 Implement `POST /api/plantillas`, `GET /api/plantillas`, `PATCH /api/plantillas/{id}` (using `payload.model_dump(exclude_unset=True)` per Hard Rule #9), and `DELETE /api/plantillas/{id}` in `backend/app/api/plantillas.py` protected by `Depends(require_roles(RolUsuario.RECEPCION))`, validating that `odontologo_id` belongs to an existing `RolUsuario.ODONTOLOGO` user (`CB-06`) and rejecting overlapping templates with HTTP `409 Conflict` (`RN-AG-01`). Verify with real-DB integration tests in `backend/tests/test_availability_engine.py` covering:
  - Expected behavior: `201 Created` on valid template, `200 OK` on list/filter, `200 OK` on partial `PATCH`, `204 No Content` on `DELETE`.
  - Business errors: `409 Conflict` on overlapping template (`09:00–13:00` vs `12:00–15:00`), `403 Forbidden` for `paciente` and `odontologo` roles (`RN-GL-01`), and `404`/`422` when `odontologo_id` is missing or not a dentist.
  - Business errors (added after `dental-agenda-auditor` review): `409 Conflict` when a `PATCH` extends a template into another same-day template of the same dentist, and `404 Not Found` on `PATCH`/`DELETE` of a non-existent `id`.
  - Edge cases: `201 Created` on contiguous templates `09:00–11:00` and `11:00–13:00` (`CB-01`), `422 Unprocessable Entity` when partial `PATCH` sets `hora_fin <= stored hora_inicio`, and `200 OK` with unchanged body when `PATCH` receives `{}` (RFC 7396 no-op).

## 4. API Layer — Free-Slot Query Endpoint (`GET /api/disponibilidad`)

- [ ] 4.1 Implement `GET /api/disponibilidad?odontologo_id=&fecha=` in `backend/app/api/disponibilidad.py` protected by `Depends(require_roles(RolUsuario.PACIENTE, RolUsuario.RECEPCION, RolUsuario.ODONTOLOGO))` and register both routers (`plantillas` and `disponibilidad`) in `backend/app/main.py`. Verify with real-DB integration tests in `backend/tests/test_availability_engine.py` using synthetic data (Hard Rule #12) covering:
  - Expected behavior: returns `200 OK` with free slots (`09:00–09:30`, `10:00–10:30`) when `09:30–10:00` has a `solicitado` or `confirmado` appointment, with zero patient PII in the response (`US-002 CA-1`, `CA-2`).
  - Business errors: returns `422 Unprocessable Entity` when `fecha` is earlier than the current date in `America/Argentina/Buenos_Aires` (`RN-GL-02`), and `404`/`422` when `odontologo_id` does not exist or is not a dentist (`CB-06`).
  - Edge cases: returns slot as free when the overlapping appointment is `cancelado` or `anulado` (`CB-03`), omits incomplete remainder slots (`09:00–10:00` with `40 min` slots returns only `09:00–09:40`, `CB-02`), blocks all three slots intersected by an off-grid `09:15–10:15` appointment (`CB-04`), and omits already elapsed morning slots when querying `fecha == today` (`CB-05`).
