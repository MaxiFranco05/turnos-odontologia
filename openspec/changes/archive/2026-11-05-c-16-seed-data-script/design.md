# Design: C-16 — Database Seed Data Script (`c-16-seed-data-script`)

## Context

`C-02` defined the core domain models (`Usuario`, `PlantillaDisponibilidad`, `Turno`). `C-03` established bcrypt password hashing in `app/infrastructure/security.py`. `C-05`, `C-06`, `C-07`, and `C-08` established availability checking, appointments state machine, and reception workflows. 

See `proposal.md` for motivation and scope, and `specs/seed-data-script/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Provide an automated, idempotent seed mechanism accessible both via command line (`python scripts/seed.py` / `python -m backend.scripts.seed`) and programmatically (`async def seed_data(session: AsyncSession, reset: bool = False, base_date: datetime.date | None = None) -> dict[str, int]`).
- Populate essential multi-role clinic accounts (`recepcion`, `odontologo`, `paciente`) with bcrypt hashes and required initial security flags (`debe_cambiar_password=True` for reception).
- Provision standard Monday-to-Friday availability templates (morning 09:00–13:00, afternoon 14:00–18:00, 30-min slots) for 2 initial dentists.
- Provision representative non-overlapping demo appointments across valid states (`solicitado`, `confirmado`, `cancelado`).
- Ensure repeated runs are strictly idempotent, causing zero constraint violations and producing identical database state.
- Adhere strictly to the 13 Hard Rules: pure synthetic test data (Hard Rule #12), SQLAlchemy 2.0 `select()` (Hard Rule #2), synchronous helpers where no I/O is performed (Hard Rule #3), and real database tests without mocks (Hard Rule #7).

**Non-Goals:**
- Executing database migrations automatically (Alembic or `Base.metadata.create_all` must run prior to seeding).
- Storing real patient or staff personally identifiable information (PII).
- Seeding thousands of historical records (stress/load testing is reserved for `C-18`).

## Decisions

### 1. Dual Entrypoint: Programmatic Coroutine and CLI Script
- **Decision**: Implement the core logic as an async function in `backend/app/infrastructure/seed.py` (or `backend/scripts/seed.py` with importable function `seed_data(session: AsyncSession, reset: bool = False) -> dict[str, int]`) and expose entrypoints at `backend/scripts/seed.py` and root `scripts/seed.py`.
- **Rationale**: Decoupling the seeding engine from CLI argument parsing allows test fixtures (`conftest.py` or `test_seed_script.py`) and application lifecycle events to trigger seeding in-memory on SQLite without subprocess invocation.
- **Alternatives considered**:
  - *CLI-only script using subprocesses in tests*: Slower, fragile across operating systems, and difficult to run inside an open SQLite in-memory test transaction.
  - *FastAPI endpoint (e.g. `POST /api/admin/seed`)*: Violates security best practices by exposing administrative reset capabilities over public HTTP interfaces.

### 2. Idempotency Strategy via SQLAlchemy 2.0 `select()` Lookups (Hard Rule #2)
- **Decision**: Before inserting each entity:
  1. For `Usuario`: query `select(Usuario).where((Usuario.email == email) | (Usuario.nro_socio == nro_socio))`. If found, reuse the existing user and skip insertion.
  2. For `PlantillaDisponibilidad`: query `select(PlantillaDisponibilidad).where(PlantillaDisponibilidad.odontologo_id == odo_id, PlantillaDisponibilidad.dia_semana == dia, PlantillaDisponibilidad.hora_inicio == start, PlantillaDisponibilidad.hora_fin == end)`. If found, skip.
  3. For `Turno`: check `select(Turno).where(Turno.odontologo_id == odo_id, Turno.inicio == inicio, Turno.fin == fin)`. If found, skip.
- **Rationale**: Guarantees complete cross-database compatibility across PostgreSQL and SQLite without dialect-specific `ON CONFLICT` nuances or sequence misalignments.

### 3. Demonstration Schedule Relative to Base Date
- **Decision**: Demonstration appointments are anchored to a deterministic reference date (e.g., next Monday relative to `base_date` or fixed date) in `America/Argentina/Buenos_Aires` timezone, ensuring they always fall within working hours and valid template slots.
- **Rationale**: Prevents expired appointments in the past or scheduling on weekends where no templates exist, ensuring seeded appointments are immediately visible in reception and dentist agendas.

### 4. Synthetic Data Profiles (Hard Rule #12)
- **Decision**: Define pure synthetic personas:
  - Reception: `recepcion@turnosodontologia.com` (password: `Admin1234!`, `debe_cambiar_password=True`)
  - Dentist 1: Dra. Sofía Martín (`sofia.martin@turnosodontologia.com`, `ODO-001`, password: `Dentist1234!`, specialty: "Odontología General")
  - Dentist 2: Dr. Lucas García (`lucas.garcia@turnosodontologia.com`, `ODO-002`, password: `Dentist1234!`, specialty: "Ortodoncia y Prótesis")
  - Patient 1: Carlos Benítez (`carlos.benitez@example.com`, `SOC-101`, password: `Patient1234!`)
  - Patient 2: Lucía Gómez (`lucia.gomez@example.com`, `SOC-102`, password: `Patient1234!`)
- **Rationale**: Fulfills Hard Rule #12 while providing clear, easily recognizable credentials for local development and QA.

## Risks / Trade-offs

- **[Risk] Foreign key integrity when resetting (`--reset`)** → **Mitigation**: When `reset=True`, delete entities in reverse dependency order (`Turno` $\rightarrow$ `PlantillaDisponibilidad` $\rightarrow$ `Usuario`) within a single database transaction.
- **[Risk] Timezone discrepancies on seed appointment timestamps** → **Mitigation**: Build all timestamps using `ZoneInfo(settings.TIMEZONE)` so datetimes are explicitly offset-aware and match the clinic's operating timezone.
