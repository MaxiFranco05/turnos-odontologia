# Design: C-08 — Reception Daily Agenda (`c-08-reception-agenda`)

## Context

`C-02` defined `Turno` and `Usuario` models with `paciente` and `odontologo` relationships. `C-03` established JWT authentication and the `require_roles(*allowed_roles)` dependency. `C-06` and `C-07` established appointment creation, state transitions, and `get_clinic_day_bounds` in `backend/app/application/turnos.py`. `C-09` implemented `GET /api/mis-turnos` for dentists.

See `proposal.md` for motivation and scope, and `specs/reception-agenda/spec.md` for normative requirements and scenarios.

## Goals / Non-Goals

**Goals:**
- Provide a Reception-only REST API endpoint (`GET /api/agenda/dia?fecha=YYYY-MM-DD[&odontologo_id=N]`) showing all appointments for a calendar date in clinic timezone (`America/Argentina/Buenos_Aires`).
- Support operational tracking of all appointment lifecycle states (`solicitado`, `confirmado`, `cancelado`, `anulado`, `presente`, `ausente`), specifically preserving patient cancellations (`cancelado`) and booking origin (`origen=online`) to satisfy `US-005 CA-1` and `CA-2`.
- Eliminate N+1 query performance penalties through SQLAlchemy 2.0 eager loading (`selectinload`) for both `Turno.paciente` and `Turno.odontologo`.
- Enforce least-privilege data projection (OWASP API3:2023 BOPLA and Hard Rule #1): strictly omit `password_hash`, `debe_cambiar_password`, or sensitive credentials in response schemas.
- Comply with all 13 Hard Rules in `AGENTS.md` (Pydantic `extra="forbid"`, SQLAlchemy 2.0 `select()`, synchronous helpers where no I/O is performed, real DB integration tests without mocks, and synthetic data).

**Non-Goals:**
- Modifying appointment states from this endpoint (handled by `PATCH /api/turnos/{id}` in `C-07`).
- Managing dentist availability templates (handled by `/api/plantillas` in `C-05`).
- Multi-day or date-range calendar views (dedicated to future portal features or `C-10`).

## Decisions

### 1. Router Location and REST Endpoint (`GET /api/agenda/dia`)
- **Decision**: Create a dedicated router in `backend/app/api/agenda.py` with prefix `/api/agenda` and register endpoint `GET /api/agenda/dia`.
- **Rationale**: `CHANGES.md` specifically prescribes `GET /api/agenda/dia?fecha=`. Grouping under `/api/agenda` keeps reception-specific scheduling views cleanly segregated from generic entity CRUD (`/api/turnos`) and dentist self-views (`/api/mis-turnos`). The path consists strictly of nouns ("agenda", "dia"), adhering to Hard Rule #8.
- **Alternatives considered**:
  - *Extending `/api/turnos` with query parameters*: Rejected because `/api/turnos` is generic, whereas the daily agenda view requires specialized projections (including dentist and patient summaries simultaneously) and distinct RBAC rules.

### 2. Eager Loading via SQLAlchemy 2.0 `selectinload`
- **Decision**: Add `find_daily_agenda(start: datetime.datetime, end: datetime.datetime, odontologo_id: int | None = None) -> list[Turno]` to `TurnoRepository` / `SqlAlchemyTurnoRepository`:
  ```python
  stmt = (
      select(Turno)
      .options(selectinload(Turno.paciente), selectinload(Turno.odontologo))
      .where(Turno.inicio >= start, Turno.inicio < end)
      .order_by(Turno.inicio, Turno.id)
  )
  if odontologo_id is not None:
      stmt = stmt.where(Turno.odontologo_id == odontologo_id)
  ```
- **Rationale**: Reception dashboards display both patient and dentist names and contact data. Relying on lazy loading would trigger $2 \times N$ secondary SQL queries, degrading response latency. Eager loading via `selectinload` performs exactly two pre-fetches in async SQLAlchemy 2.0, completely avoiding greenlet exceptions and query bloat.

### 3. Pydantic v2 Response Schemas with Strict Extra Forbid (Hard Rule #1 & OWASP BOPLA)
- **Decision**: Define projection models in `backend/app/api/agenda.py`:
  - `AgendaPacienteResponse`: `id: int`, `nombre: str`, `nro_socio: str | None`, `email: str | None`.
  - `AgendaOdontologoResponse`: `id: int`, `nombre: str`, `email: str | None`.
  - `AgendaTurnoDiaResponse`: `id: int`, `paciente_id: int`, `odontologo_id: int`, `inicio: datetime.datetime`, `fin: datetime.datetime`, `motivo: str`, `estado: EstadoTurno`, `origen: OrigenTurno`, `paciente: AgendaPacienteResponse`, `odontologo: AgendaOdontologoResponse`.
  - All schemas specify `model_config = ConfigDict(extra="forbid", from_attributes=True)`.
- **Rationale**: Fulfills Hard Rule #1. Prevents Broken Object Property Level Authorization (BOPLA) by guaranteeing that sensitive user fields (`password_hash`, `debe_cambiar_password`, internal flags) are never serialized to the client.

### 4. Dentist Validation and Role Check (`CB-06`)
- **Decision**: When `odontologo_id` is supplied in the query string:
  1. Query `SqlAlchemyUsuarioRepository.get_by_id(odontologo_id)`.
  2. If the user does not exist, raise HTTP `404 Not Found`.
  3. If the user exists but `user.rol != RolUsuario.ODONTOLOGO`, raise HTTP `422 Unprocessable Entity`.
- **Rationale**: Matches the domain edge-case standard established in `C-05` and `C-06`, preventing ambiguous empty agenda results caused by querying invalid user IDs.

### 5. Timezone-Aware Day Boundaries
- **Decision**: Reuse `get_clinic_day_bounds(fecha, settings.TIMEZONE)` from `backend/app/application/turnos.py` to calculate `[day_start, day_end)` where `day_start = fecha 00:00:00` and `day_end = (fecha + 1 day) 00:00:00` in `ZoneInfo(settings.TIMEZONE)`.
- **Rationale**: `get_clinic_day_bounds` is a tested, pure synchronous helper (Hard Rule #3) that avoids duplicate timezone logic and handles date boundary math consistently.

## Risks / Trade-offs

- **[Risk] Datetime offset comparison issues across SQLite and PostgreSQL** → **Mitigation**: `get_clinic_day_bounds` returns timezone-aware datetimes with `ZoneInfo(settings.TIMEZONE)`. `Turno.inicio` and `Turno.fin` are stored with timezone awareness (`DateTime(timezone=True)`). If SQLite returns naive datetimes in tests, repository queries against ISO string intervals or normalized timestamps ensure correct filtering without TypeError.
