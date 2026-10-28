# Proposal: C-02 Core Models

## Why

The appointment management system needs its core persistence layer and domain entities established in PostgreSQL to support authentication, availability calculations, and appointment reservations. Without explicit relational models, foreign key cascades, check constraints, and anti-overlap invariants defined at the database and ORM level, the system cannot safely guarantee business rules like dentist schedule non-collision (RN-AG-01) or role-based account constraints.

## What Changes

- Create declarative SQLAlchemy 2.0 models under `backend/app/domain/models/`:
  - `Usuario`: multi-role accounts (paciente, recepcion, odontologo), credential storage, socio/email uniqueness.
  - `PlantillaDisponibilidad`: weekly availability templates per dentist (`dia_semana`, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`, `prestacion`).
  - `Turno`: appointment reservations with status enum (`solicitado`, `confirmado`, `anulado`, `cancelado`, `presente`, `ausente`), origin (`online`, `manual`), and time window `[inicio, fin)`.
- Define base declarative mixins (`TimestampMixin` with timezone-aware `creado_en` and `actualizado_en`).
- Define database-level constraints:
  - Check constraint: `hora_fin > hora_inicio` and `duracion_slot_minutos > 0` on `PlantillaDisponibilidad`.
  - Check constraint: `fin > inicio` on `Turno`.
  - Anti-overlap constraint/index: prevent overlapping appointments for the same dentist for non-cancelled/non-annulled appointments (RN-AG-01).
  - Check constraint or validation ensuring either `email` or `nro_socio` is populated for `Usuario`.
- Generate and execute Alembic migration `002_create_core_tables.py` creating tables, foreign keys, indexes, and constraints.
- Define base generic repository pattern in `backend/app/domain/repositories/` and SQLAlchemy implementation in `backend/app/infrastructure/repositories/`.

## Capabilities

### New Capabilities

- `core-data-models`: Relational entities, schema definitions, and persistence repositories for users, dentist availability templates, and appointments.
- `appointment-integrity`: Relational and domain invariants ensuring appointment time windows are strictly ordered (`fin > inicio`) and prevent overlapping schedules for the same dentist (RN-AG-01).

### Modified Capabilities

None.

## Impact

- Affected modules: `backend/app/domain/models/`, `backend/app/domain/repositories/`, `backend/app/infrastructure/repositories/`, `backend/alembic/versions/`.
- Dependencies: Extends `c-01-foundation-setup` async SQLAlchemy 2.0 runtime.
- Breaking changes: None.
