# Tasks: C-01 Foundation Setup

## 1. Directory Structure and Environment Scaffolding

- [x] 1.1 Create canonical backend directory layout (`backend/app/{domain,application,infrastructure,api}`, `backend/tests/`) and remove orphaned legacy files in `src/backend`. Verify folder structure exists.
- [x] 1.2 Define `pyproject.toml` or `requirements.txt` with locked dependencies (`fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pytest`, `pytest-asyncio`, `httpx`). Verify package installation without conflicts.
- [x] 1.3 Create `.env.example` documenting required variables (`DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `CANCEL_MIN_HOURS`, `TIMEZONE`). Verify `.env.example` matches KB-08.

## 2. Typed Configuration Management

- [x] 2.1 Write unit tests for configuration loading (`tests/test_config.py`), covering valid settings, missing required fields, and rejection of undeclared fields (`extra="forbid"`). Verify tests fail initially (TDD RED).
- [x] 2.2 Implement `backend/app/infrastructure/config.py` using Pydantic Settings (`BaseSettings`) with `ConfigDict(extra="forbid")` and validated URL parsing. Verify tests pass (TDD GREEN).

## 3. Asynchronous Database Engine and Lifespan

- [x] 3.1 Write tests for database session lifecycle and app lifespan (`tests/test_database.py`), verifying connection acquisition and engine disposal. Verify tests fail initially (TDD RED).
- [x] 3.2 Implement asynchronous engine creation and session factory in `backend/app/infrastructure/database.py` with SQLAlchemy 2.0 `create_async_engine` and `async_sessionmaker`. Verify tests pass (TDD GREEN).
- [x] 3.3 Implement FastAPI application factory and `@asynccontextmanager` lifespan in `backend/app/main.py`, binding engine and sessionmaker to `app.state`. Verify lifespan teardown tests pass.

## 4. Health Monitoring Probes

- [x] 4.1 Write API integration tests for health endpoints (`tests/test_health.py`), checking `GET /health/live` returns 200 and `GET /health/ready` returns 200 on DB success and 503 on DB connection failure. Verify tests fail initially (TDD RED).
- [x] 4.2 Implement health router in `backend/app/api/health.py` and register it with the FastAPI app. Verify all health tests pass (TDD GREEN).

## 5. Database Migrations Setup

- [x] 5.1 Initialize and configure Alembic for async SQLAlchemy in `backend/alembic/` and `backend/alembic.ini`. Verify `alembic current` runs without errors.
- [x] 5.2 Create initial baseline migration. Verify `alembic upgrade head` executes cleanly against test database.

## 6. Docker Infrastructure and Container Healthchecks

- [x] 6.1 Create `backend/Dockerfile` with multi-stage build, unprivileged user, and explicit healthcheck instruction. Verify image builds successfully.
- [x] 6.2 Create root `docker-compose.yml` with `api` and `postgres` services, configuring resource limits and Docker healthchecks according to Hard Rule #10. Verify `docker compose config` validates syntax.

## Workflow follow-up

- Review and approve the proposed change artifacts.
- Execute `/opsx-apply c-01-foundation-setup` under Strict TDD.
