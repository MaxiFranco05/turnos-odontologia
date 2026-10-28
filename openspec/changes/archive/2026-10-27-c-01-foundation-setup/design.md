# Design: C-01 Foundation Setup

## Context

The system must support an appointment booking platform with strict concurrency and state transition rules. To prevent architectural debt and runtime regressions from day one, we must establish a verified backend foundation adhering strictly to the architectural patterns in KB-08 and the 13 project hard rules in `AGENTS.md`. Previous attempts left an uncoordinated prototype in `src/backend/` that violated core project patterns; this design establishes the canonical foundation structure under `backend/app/`.

## Goals / Non-Goals

**Goals:**
- Provide a clean, modular directory structure (`backend/app/{domain,application,infrastructure,api}`) aligned with clean architecture.
- Enforce strict typed configuration via Pydantic Settings (`model_config = ConfigDict(extra="forbid")`).
- Establish asynchronous database connectivity with SQLAlchemy 2.0 (`create_async_engine`, `async_sessionmaker`, `AsyncSession`) driven by `asyncpg`.
- Implement lifespan management attached to `app.state` with proper connection pooling and graceful disposal on shutdown.
- Implement reliable `/health/live` and `/health/ready` endpoints verifying database ping (`SELECT 1`) with timeout protection and HTTP 503 error handling.
- Setup Alembic async migration scaffold with an initial baseline migration.
- Provide production-ready `docker-compose.yml` with healthchecks, restart policies, and resource boundaries.
- Set up pytest test environment with Strict TDD guidelines.

**Non-Goals:**
- Implementation of domain entities and business models (deferred to C-02 `core-models`).
- Implementation of authentication and token issuance (deferred to C-03 `auth-jwt`).
- Full frontend application scaffolding and routing (deferred to C-11 `frontend-scaffold`).
- Seed data scripts (deferred to C-16 `seed-data-script`).

## Decisions

### 1. Asynchronous Database Driver: asyncpg vs psycopg3
- **Decision**: Use `asyncpg` with `postgresql+asyncpg://` protocol and SQLAlchemy 2.0 async engine.
- **Rationale**: `asyncpg` is the benchmark async driver for PostgreSQL in high-performance Python ASGI applications, with native binary protocol support and proven reliability under concurrency.
- **Alternatives considered**:
  - `psycopg3`: Good async support, but `asyncpg` has deeper ecosystem tooling and integration patterns in FastAPI enterprise setups.
  - Synchronous `psycopg2`: Violates non-blocking I/O requirements for FastAPI endpoints handling concurrent slot reservation checks.

### 2. Configuration Strategy: Pydantic BaseSettings with `extra="forbid"`
- **Decision**: Centralize all environment parameters in `Settings(BaseSettings)` with `extra="forbid"` in `model_config`.
- **Rationale**: Direct compliance with Project Hard Rule #1. Prevents typo-based silent bugs (e.g. `DATA_BASE_URL` vs `DATABASE_URL`) by failing fast at process boot.
- **Alternatives considered**:
  - `os.environ.get()`: Untyped, no validation, prone to silent runtime failures.
  - `python-decouple`: Less type coercion capability compared to Pydantic v2.

### 3. Application State and Lifespan Pattern
- **Decision**: Manage async engine and session factory exclusively inside FastAPI's `@asynccontextmanager` lifespan handler, stored on `app.state.engine` and `app.state.session_factory`.
- **Rationale**: Avoids module-level global state, ensures deterministic initialization order, and guarantees that `await engine.dispose()` runs on SIGTERM/shutdown.
- **Alternatives considered**:
  - Deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")`: Deprecated in current FastAPI versions and lacks single-context exception handling.

### 4. Healthcheck Contract
- **Decision**: Separate `/health/live` (shallow, returns 200 immediately) and `/health/ready` (deep, executes `SELECT 1` with a 2-second timeout against PostgreSQL).
- **Rationale**: Kubernetes and Docker need distinct probes: liveness detects deadlocks/crashes, while readiness prevents traffic routing before the database is connected or during transient network partitions.
- **Alternatives considered**:
  - Single `/health` endpoint: Does not allow orchestrators to distinguish between a dead process and an temporarily unavailable database.

### 5. Docker Compose Standards
- **Decision**: Define healthchecks with `interval`, `timeout`, `retries`, and `start_period`, along with `deploy.resources.limits` for both `api` and `postgres` containers.
- **Rationale**: Complies with Project Hard Rule #10. Ensures containers report true readiness and prevents memory exhaustion on shared development machines.

## Risks / Trade-offs

- **[Risk]** Startup failure if PostgreSQL container takes longer to accept connections than the API startup check.
  → **Mitigation**: Implement Docker Compose `depends_on` with `condition: service_healthy` on the postgres service, and make the app lifespan resilient with retries or readiness-only DB gating.
- **[Risk]** Discrepancy between old prototype files in `src/backend` and canonical `backend/app`.
  → **Mitigation**: Migrate or clean up `src/` to ensure single source of truth under `backend/app` without ambiguous imports.
