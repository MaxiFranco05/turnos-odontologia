# Design: C-05 — Availability Engine & Schedule Templates (`c-05-availability-engine`)

## Context

`C-02` (`core-models`) already created the `PlantillaDisponibilidad` and `Turno` SQLAlchemy 2.0 models, `SqlAlchemyPlantillaRepository` (`find_by_dentist`, `find_by_dentist_and_day`), and `SqlAlchemyTurnoRepository` (`find_by_dentist_range`, `find_overlapping`). `C-03` and `C-04` established `get_current_user`, `require_password_changed`, and `require_roles(*allowed_roles)` in `backend/app/api/deps.py`.

See `proposal.md` for motivation and scope, and `specs/availability-engine/spec.md` for normative requirements and scenarios.

## Goals / Non-Goals

**Goals:**
- Provide a Reception-only REST API (`/api/plantillas`) for creating, listing, partially updating (`PATCH`), and deleting `PlantillaDisponibilidad` records while enforcing same-dentist, same-day interval non-overlap (`RN-AG-01`).
- Provide an authenticated REST endpoint (`GET /api/disponibilidad`) that derives free slots on the fly from `PlantillaDisponibilidad` minus active `Turno` records in the configured clinic timezone (`RN-AG-02`, `RN-GL-02`).
- Strictly comply with all 13 Hard Rules in `AGENTS.md` (Pydantic `extra="forbid"`, SQLAlchemy 2.0 `select()`, sync `def` for pure in-memory slot math, `PATCH` instead of `PUT` for partial updates, real DB tests without mocks, and synthetic test data).

**Non-Goals:**
- Creating or booking appointments (`POST /api/turnos` belongs to `C-06`).
- Managing dentist box/chair assignment (the v1 data model in `04_modelo_de_datos.md` scopes availability templates and overlap invariants per `odontologo_id`).
- Pre-generating empty `Turno` rows in PostgreSQL (explicitly forbidden by `RN-AG-02` and `08_arquitectura_propuesta.md`).

## Decisions

### 1. HTTP `PATCH /api/plantillas/{id}` with `model_dump(exclude_unset=True)` instead of `PUT`
- **Decision**: Expose `PATCH /api/plantillas/{id}` for template modifications and validate the merged attributes (`stored_template` + `payload.model_dump(exclude_unset=True)`).
- **Rationale**: `CHANGES.md` originally listed `POST/GET/PUT/DELETE /api/plantillas`, which conflicts with **Hard Rule #9** (`NUNCA PUT para updates parciales → PATCH`). Inspecting official FastAPI documentation via the **`playwright` MCP** (`browser_navigate` to `https://fastapi.tiangolo.com/tutorial/body-updates/`) confirmed the idiomatic pattern: define `PlantillaUpdate` with optional fields and `ConfigDict(extra="forbid")`, extract only client-sent fields via `payload.model_dump(exclude_unset=True)`, merge them onto the loaded entity attributes, verify `effective_hora_fin > effective_hora_inicio`, and run overlap detection excluding `template.id`.
- **Alternatives considered**:
  - *Full replacement via `PUT`*: Rejected because partial updates are standard for adjusting slot duration or end time from Reception UI (`C-14`) and `AGENTS.md` Hard Rule #9 mandates `PATCH`.
  - *Validating `hora_fin > hora_inicio` only inside `PlantillaUpdate`*: Insufficient when a client sends only `{"hora_fin": "08:00"}` without `hora_inicio`; validation must also run against the merged state.
- **Empty payload `{}`** (added after `dental-agenda-auditor` review): treated as an idempotent no-op returning `200 OK` with the unchanged template, following JSON Merge Patch semantics (RFC 7396) — a technical, not a domain, decision. Rejecting with `422` was considered but adds no protection since no state changes.

### 2. Server-Side Template Overlap Check via SQLAlchemy 2.0 `select()`
- **Decision**: Add `find_overlapping_templates(odontologo_id, dia_semana, hora_inicio, hora_fin, exclude_id=None)` to `PlantillaRepository` / `SqlAlchemyPlantillaRepository` using the half-open interval intersection predicate:
  ```python
  PlantillaDisponibilidad.odontologo_id == odontologo_id,
  PlantillaDisponibilidad.dia_semana == dia_semana,
  PlantillaDisponibilidad.hora_inicio < hora_fin,
  PlantillaDisponibilidad.hora_fin > hora_inicio,
  ```
- **Rationale**: Using strict inequalities (`<` and `>`) treats intervals as half-open `[hora_inicio, hora_fin)`. Consequently, contiguous templates such as `09:00–11:00` and `11:00–13:00` (`CB-01`) do not collide (`09:00 < 13:00` and `11:00 > 11:00` is `False`), whereas any partial or total intersection returns a conflict and triggers HTTP `409 Conflict`.
- **Alternatives considered**:
  - *Database exclusion constraint on `Time`*: SQLite (used in local test suite) lacks PostgreSQL's `tsrange`/`timerange` GiST exclusion constraints, so repository-level transactional check with `select()` guarantees identical behavior across SQLite and PostgreSQL.

### 3. Pure Synchronous Slot-Derivation Function (`def calculate_free_slots`)
- **Decision**: Implement the slot partitioning and filtering algorithm as a pure synchronous function (`def calculate_free_slots(...) -> list[SlotDisponible]`) in `backend/app/application/availability.py`, called by the async endpoint after fetching templates and appointments from the database.
- **Rationale**: **Hard Rule #3** states `NUNCA async def sin I/O real async → preferir def sincrónico`. Once the repository awaits `find_by_dentist_and_day` and `find_by_dentist_range`, computing slots in memory performs zero I/O. Making `calculate_free_slots` a pure `def` function obeys Hard Rule #3 and makes unit/edge-case verification (`CB-01` to `CB-05`) deterministic.
- **Algorithm details**:
  1. Resolve clinic timezone via `ZoneInfo(settings.TIMEZONE)` (`America/Argentina/Buenos_Aires`) and current clinic timestamp `now_local`.
  2. If `fecha < now_local.date()`, raise `422 Unprocessable Entity` (`RN-GL-02`).
  3. Filter fetched `Turno` records for that date to active blocking states (`estado not in {EstadoTurno.CANCELADO, EstadoTurno.ANULADO}`, `CB-03`).
  4. For each template on `fecha.weekday()` (ordered by `hora_inicio`):
     - Combine `fecha` and `template.hora_inicio` / `template.hora_fin` with `ZoneInfo(settings.TIMEZONE)`.
     - Step forward by `timedelta(minutes=template.duracion_slot_minutos)` while `slot_inicio + delta <= template_fin` (discarding any trailing remainder smaller than `duracion_slot_minutos`, `CB-02`).
     - Skip the slot if `fecha == now_local.date()` and `slot_inicio <= now_local` (`CB-05`).
     - Skip the slot if any active `Turno` satisfies `turno.inicio < slot_fin and turno.fin > slot_inicio` (`CB-04`).
     - Append `{inicio: slot_inicio, fin: slot_fin, odontologo_id, prestacion: template.prestacion}` to the result list.

### 4. Endpoint Authorization Boundaries
- **Decision**:
  - `/api/plantillas` (`POST`, `GET`, `PATCH`, `DELETE`): Protected with `Depends(require_roles(RolUsuario.RECEPCION))`.
  - `/api/disponibilidad` (`GET`): Protected with `Depends(require_roles(RolUsuario.PACIENTE, RolUsuario.RECEPCION, RolUsuario.ODONTOLOGO))` (which also enforces `debe_cambiar_password == False` via `C-04`).
- **Rationale**: Matches `03_actores_y_roles.md` and `CHANGES.md` (`C-05` scope: CRUD plantillas solo recepción; `GET /api/disponibilidad` used by patients in `US-002` and reception).

## Risks / Trade-offs

- **[Risk] Timezone-naive vs. timezone-aware `Turno.inicio`/`Turno.fin` comparisons in SQLite test runs** → **Mitigation**: Normalize any naive datetime returned by SQLite into `ZoneInfo(settings.TIMEZONE)` (or compare in UTC/clinic-aware timestamps consistently) inside `calculate_free_slots` so interval comparisons never raise `TypeError: can't compare offset-naive and offset-aware datetimes`.
- **[Risk] Concurrent template creation for the same dentist and day** → **Mitigation**: Execute the overlap query and `session.flush()` inside the same database transaction boundary before committing.
