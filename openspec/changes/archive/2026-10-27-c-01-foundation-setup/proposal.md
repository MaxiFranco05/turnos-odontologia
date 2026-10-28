# Proposal: C-01 Foundation Setup

## Why

The appointment scheduling system requires a robust, reproducible, and verifiable operational foundation before domain logic and models can be built. Establishing strict configuration management, async database connectivity, health check probes, containerized local infrastructure, and testing harnesses upfront prevents architectural divergence, enforces the project's hard stack rules (Pydantic `extra="forbid"`, SQLAlchemy 2.0 async, container healthchecks), and ensures clean CI/local development.

## What Changes

- Scaffold modular project directory layout according to KB-08: `backend/app/{domain,application,infrastructure,api}`, `backend/tests/`, `frontend/`, and root orchestrations.
- Implement typed configuration module using Pydantic Settings (`BaseSettings`) enforcing `extra="forbid"` and strict validation of database credentials, timezone, and operational timeouts.
- Configure asynchronous database engine and session factory with SQLAlchemy 2.0 (`asyncpg`) and async lifespan management in FastAPI (`app.state`).
- Implement health monitoring endpoints (`/health/live` and `/health/ready`) to report process liveness and transactional database readiness (returning HTTP 503 upon database degradation).
- Configure Alembic migrations environment for asynchronous PostgreSQL schema evolution.
- Provide Docker Compose configuration with healthchecks, restart policies, and resource constraints for PostgreSQL and API services.
- Establish baseline test suite (pytest + pytest-asyncio) under Strict TDD rules.

## Capabilities

### New Capabilities

- `app-runtime`: Application lifecycle management, strict environment settings loading, and asynchronous database engine/session lifecycle with graceful shutdown.
- `health-monitoring`: Standardized HTTP liveness and readiness probe endpoints verifying process operational state and live database connectivity.

### Modified Capabilities

None. (Initial foundation change).

## Impact

- Affected systems: Project foundation, backend application core, docker configuration, database migrations baseline.
- Dependencies introduced: `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pytest`, `pytest-asyncio`, `httpx`.
- Breaking changes: None (new baseline).
