# Tasks: C-02 Core Models

## 1. Base Declarative Mapping and Mixins

- [x] 1.1 Create test suite for base mixins and enums (`tests/test_base_models.py`), verifying timestamp population and enum membership (`RolUsuario`, `EstadoTurno`, `OrigenTurno`). Verify tests fail initially (TDD RED).
- [x] 1.2 Implement `backend/app/domain/models/base.py` defining `Base(DeclarativeBase)` and `TimestampMixin` with timezone-aware datetime attributes. Verify tests pass (TDD GREEN).
- [x] 1.3 Implement domain enums in `backend/app/domain/models/enums.py` matching KB-04 and KB-05 definitions. Verify enum tests pass.

## 2. Core Relational Entities

- [x] 2.1 Write unit tests for `Usuario` entity (`tests/test_user_model.py`), testing field constraints, credential flags, and identifier requirement (email or socio number). Verify tests fail initially (TDD RED).
- [x] 2.2 Implement `Usuario` model in `backend/app/domain/models/usuario.py`. Verify tests pass (TDD GREEN).
- [x] 2.3 Write unit tests for `PlantillaDisponibilidad` and `Turno` entities (`tests/test_appointment_models.py`), verifying foreign keys, relationships, and check constraints (`fin > inicio`, `hora_fin > hora_inicio`). Verify tests fail initially (TDD RED).
- [x] 2.4 Implement `PlantillaDisponibilidad` in `backend/app/domain/models/plantilla.py` and `Turno` in `backend/app/domain/models/turno.py`. Verify tests pass (TDD GREEN).

## 3. Anti-Overlap Invariant and Constraints

- [x] 3.1 Write tests verifying anti-overlap invariant enforcement (`tests/test_overlap_constraint.py`), asserting that overlapping active appointments for the same dentist are rejected, while cancelled/annulled overlaps are accepted. Verify tests fail initially (TDD RED).
- [x] 3.2 Implement anti-overlap constraint/validation logic in the model and repository layers adhering to RN-AG-01. Verify tests pass (TDD GREEN).

## 4. Generic and Specific Async Repositories

- [x] 4.1 Write tests for repository CRUD and lookup methods (`tests/test_repositories.py`), verifying async `select()` queries, filtering by identifier, and appointment range queries. Verify tests fail initially (TDD RED).
- [x] 4.2 Implement `BaseRepository` interface in `backend/app/domain/repositories/base.py` and SQLAlchemy async implementation in `backend/app/infrastructure/repositories/base.py`. Verify tests pass (TDD GREEN).
- [x] 4.3 Implement `UsuarioRepository` and `TurnoRepository` in `backend/app/infrastructure/repositories/` with composite query methods (`find_by_identifier`, `find_by_dentist_range`). Verify tests pass (TDD GREEN).

## 5. Alembic Database Migration

- [x] 5.1 Update `backend/alembic/env.py` to bind `target_metadata = Base.metadata`. Verify metadata is properly resolved.
- [x] 5.2 Generate migration script `backend/alembic/versions/*_create_core_tables.py` containing tables, check constraints, indexes, and foreign keys. Verify `alembic upgrade head` executes cleanly on test database.

## Workflow follow-up

- Review and approve planning artifacts.
- Execute `/opsx-apply c-02-core-models` under Strict TDD.
