# Design: C-02 Core Models

## Context

Following C-01 (foundation runtime and database connectivity), this change introduces the core domain and relational entities that form the backbone of the entire clinic management application. Every downstream change—authentication (C-03), availability calculations (C-05), appointment booking (C-06), and agenda dashboards (C-08/C-09)—depends on the data schemas and integrity guarantees established here.

## Goals / Non-Goals

**Goals:**
- Define typed SQLAlchemy 2.0 declarative models using modern `Mapped[...]` and `mapped_column(...)` patterns (Hard Rule #2).
- Establish multi-role user accounts (`Usuario`), weekly availability templates (`PlantillaDisponibilidad`), and appointment reservations (`Turno`).
- Provide explicit enums for roles (`RolUsuario`), appointment states (`EstadoTurno`), and appointment booking origins (`OrigenTurno`).
- Enforce strict database check constraints:
  - Valid user identifiers: `(email IS NOT NULL) OR (nro_socio IS NOT NULL)`.
  - Valid template time bounds: `hora_fin > hora_inicio` and `duracion_slot_minutos > 0`.
  - Valid appointment duration: `fin > inicio`.
- Provide indexing on key query paths: `(odontologo_id, inicio)` and `(paciente_id, inicio)`.
- Provide anti-overlap validation (RN-AG-01) for dentist appointments.
- Implement reusable async repository interfaces and base implementations using SQLAlchemy 2.0 `select()` statements.
- Generate and verify Alembic migration `002_create_core_tables.py`.

**Non-Goals:**
- Authentication endpoints, JWT generation, or password hashing verification (deferred to C-03 `auth-jwt`).
- Dynamic slot availability generation algorithm (deferred to C-05 `availability-engine`).
- HTTP endpoints for appointment scheduling or state machine transitions (deferred to C-06 and C-07).

## Decisions

### 1. SQLAlchemy 2.0 Declarative Mapping Standard
- **Decision**: Use `Mapped[...]` and `mapped_column(...)` extending a shared `Base(DeclarativeBase)` class.
- **Rationale**: Modern SQLAlchemy 2.0 typing ensures strict static analysis and compatibility with mypy/IDE autocompletion, completely deprecating legacy `Column` syntax.
- **Alternatives considered**:
  - Legacy SQLAlchemy 1.4 mapping: Prone to typing errors and incompatible with modern FastAPI/Pydantic integrations.

### 2. Timezone-Aware Timestamps
- **Decision**: Store all appointment timestamps and audit mixins using `DateTime(timezone=True)` with UTC persistence, interpreting local consultant schedules according to the configured `TIMEZONE` (America/Argentina/Buenos_Aires).
- **Rationale**: Eliminates daylight-saving ambiguities and guarantees clean comparisons across system boundaries.
- **Alternatives considered**:
  - Naive datetimes: Prone to silent shift errors when clients and database reside in different timezones.

### 3. Anti-Overlap Invariant (RN-AG-01) Strategy
- **Decision**: Multi-tier enforcement:
  1. Relational level: PostgreSQL GiST exclusion constraint (`tstzrange(inicio, fin, '[)') WITH &&, odontologo_id WITH =`) filtering out cancelled/annulled appointments.
  2. Repository/Domain level: Invariant check during slot booking queries (`select(Turno).where(...)`) using serializable transactions or `FOR UPDATE` locking.
  3. Dialect fallback: For SQLite unit testing where `btree_gist` is unavailable, check queries or trigger mechanisms maintain test coverage without DB mocking (Hard Rule #7).
- **Rationale**: Fulfills differential requirement RN-AG-01 as an absolute server-side invariant.

### 4. Repository Layer Architecture
- **Decision**: Place generic interfaces (`BaseRepository`, `UsuarioRepository`, `TurnoRepository`) in `backend/app/domain/repositories/` and SQLAlchemy implementations in `backend/app/infrastructure/repositories/`.
- **Rationale**: Preserves clean architecture separation of concerns; use cases in future changes consume domain interfaces rather than coupled ORM sessions.

## Risks / Trade-offs

- **[Risk]** GiST exclusion constraints in PostgreSQL require the `btree_gist` extension.
  → **Mitigation**: Add `CREATE EXTENSION IF NOT EXISTS btree_gist;` to the Alembic migration with dialect condition checking.
- **[Risk]** SQLite test environment incompatibility with PostgreSQL specific extensions.
  → **Mitigation**: Design Alembic migrations and repository checks to be dialect-aware, running full PostgreSQL integration in Docker and standard unit tests in SQLite.
