# Proposal: C-05 — Availability Engine & Schedule Templates (`c-05-availability-engine`)

## Why

With the core domain models (`Usuario`, `PlantillaDisponibilidad`, `Turno`) implemented in `C-02` and JWT/RBAC authentication (`get_current_user`, `require_roles`) established in `C-03` and `C-04`, the system still lacks the administrative endpoints for Reception to configure each dentist's weekly availability templates (`PlantillaDisponibilidad`) and the slot-derivation engine (`GET /api/disponibilidad`) for patients and receptionists to query bookable time slots (`US-002`). Without this capability, `C-06` (`appointment-request`) cannot verify whether a requested appointment falls within a valid template slot (`RN-AG-02`) nor can `C-13` (`patient-features`) or `C-14` (`reception-features`) display available schedules.

## What Changes

- **Availability Template CRUD (`/api/plantillas`)**:
  - `POST /api/plantillas` (restricted to `RolUsuario.RECEPCION`): Creates a weekly `PlantillaDisponibilidad` for a target user with role `odontologo`, validating `dia_semana` (`0..6`), `hora_fin > hora_inicio`, `duracion_slot_minutos > 0`, and ensuring no time-window overlap (`[hora_inicio, hora_fin)`) with existing templates of the same dentist on the same `dia_semana` (`RN-AG-01`, Hard Rule #13).
  - `GET /api/plantillas` (restricted to `RolUsuario.RECEPCION`, with optional `odontologo_id` query filter): Lists configured availability templates ordered by `dia_semana` and `hora_inicio`.
  - `PATCH /api/plantillas/{id}` (restricted to `RolUsuario.RECEPCION`): Performs partial updates using `model_dump(exclude_unset=True)` (enforcing Hard Rule #9 instead of the legacy `PUT` noted in `CHANGES.md`), validating the merged time interval (`effective_hora_fin > effective_hora_inicio`) and re-checking non-overlap against other templates for the same dentist and day.
  - `DELETE /api/plantillas/{id}` (restricted to `RolUsuario.RECEPCION`): Removes an availability template (`204 No Content`).
- **Dynamic Free-Slot Calculation (`GET /api/disponibilidad`)**:
  - Accepts required query parameters `odontologo_id` (`int`) and `fecha` (`datetime.date`), accessible to authenticated users with a completed password change (`paciente`, `recepcion`, `odontologo`).
  - Validates that the target `odontologo_id` belongs to an existing user with `rol == RolUsuario.ODONTOLOGO` and that `fecha` is not in the past relative to the clinic timezone (`TIMEZONE=America/Argentina/Buenos_Aires`, `RN-GL-02`).
  - Derives bookable slots purely from the dentist's templates for `fecha.weekday()` (`0=Monday .. 6=Sunday`) divided into contiguous intervals of `duracion_slot_minutos` (`slot_inicio + duracion <= hora_fin`), subtracting any slot intersecting `[turno.inicio, turno.fin)` of an existing appointment in state `solicitado`, `confirmado`, `presente`, or `ausente` (`RN-AG-01`, `RN-AG-02`), while releasing slots whose appointments are in state `cancelado` or `anulado` (`RN-TU-04`).
  - Filters out slots whose start timestamp has already elapsed when `fecha` equals the current clinic date (`RN-GL-02`).
  - Returns only free slot boundaries (`inicio`, `fin`, `prestacion`) without exposing any patient information (`US-002 CA-2`, Hard Rule #12).

## Capabilities

### New Capabilities
- `availability-engine`: Reception-only CRUD management of weekly dentist availability templates (`/api/plantillas`) with same-day non-overlap enforcement, and real-time derivation of bookable appointment slots (`/api/disponibilidad`) from templates minus active appointments in the clinic timezone.

### Modified Capabilities
<!-- No existing capability requirements are modified. -->

## Impact

- **Domain & Infrastructure Repositories**: Extends `PlantillaRepository` (`backend/app/domain/repositories/plantilla.py`) and `SqlAlchemyPlantillaRepository` (`backend/app/infrastructure/repositories/plantilla.py`) with `find_overlapping_template(...)` using SQLAlchemy 2.0 `select()` (Hard Rule #2).
- **Application / Domain Service**: Adds pure synchronous slot-partitioning helper (`def calculate_free_slots(...)`, respecting Hard Rule #3) and template/availability orchestration in `backend/app/application/availability.py`.
- **API & Pydantic v2 Schemas**: Adds `backend/app/api/plantillas.py` and `backend/app/api/disponibilidad.py` with strict `ConfigDict(extra="forbid")` schemas and `@model_validator(mode="after")` (Hard Rule #1), registered in `backend/app/main.py`.
- **Tests**: Adds `backend/tests/test_availability_engine.py` against a real database session without mocks (Hard Rule #7) and using 100% synthetic test data (Hard Rule #12).
