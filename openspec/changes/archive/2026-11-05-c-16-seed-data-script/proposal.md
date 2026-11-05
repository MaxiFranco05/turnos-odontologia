# Proposal: C-16 — Database Seed Data Script (`c-16-seed-data-script`)

## Why

Setting up the clinic booking system for local development, automated testing, manual demonstrations, and initial deployment requires consistent, idempotent database provisioning. Without a dedicated seed script, developers and administrators must manually create reception accounts, dentists, and weekly availability templates via raw database queries or manual API calls, risking inconsistent schemas, invalid role configurations, and constraint violations.

## What Changes

- Create a reusable, idempotent database seed script located at `backend/scripts/seed.py` (and root symlink/wrapper `scripts/seed.py`) executable via CLI (`python scripts/seed.py` or `python -m backend.scripts.seed`).
- Provide an async programmatic interface `seed_data(session: AsyncSession, reset: bool = False) -> dict[str, int]` for integration into test fixtures, startup migrations, and container provisioning.
- Seed essential administrative and operational accounts with bcrypt-hashed passwords and synthetic test data (enforcing Hard Rule #12):
  - **Receptionist account**: `recepcion@turnosodontologia.com` with `rol=RolUsuario.RECEPCION`, `debe_cambiar_password=True`, and `perfil_completo=True`.
  - **Dentist accounts**: Dra. Sofía Martín (`ODO-001`) and Dr. Lucas García (`ODO-002`) with `rol=RolUsuario.ODONTOLOGO`, `perfil_completo=True`, and distinct specialties (`prestacion`).
  - **Patient accounts**: Carlos Benítez (`SOC-101`) and Lucía Gómez (`SOC-102`) with `rol=RolUsuario.PACIENTE` and `perfil_completo=True`.
- Seed recurring weekly availability templates (`PlantillaDisponibilidad`) for both dentists:
  - Monday through Friday (days 0–4), Morning (09:00–13:00) and Afternoon (14:00–18:00) blocks, with 30-minute slot durations (`duracion_slot_minutos=30`), adhering to `RN-AG-01` (no overlapping intervals).
- Seed realistic demonstration appointments across varied lifecycle states (`solicitado`, `confirmado`, `cancelado`) without schedule overlap (Hard Rule #13).
- Guarantee strict idempotency: re-running the script multiple times produces identical state without duplicate records or primary key/unique constraint exceptions.
- Add an automated test suite (`backend/tests/test_seed_script.py`) exercising the seeding logic against a real database without mocks (Hard Rule #7), validating idempotency, user credentials, and API discoverability.

## Capabilities

### New Capabilities
- `seed-data-script`: Idempotent database provisioning script and programmatic seeder for clinic accounts (reception, dentists, patients), recurring weekly availability templates, and demonstration appointments.

### Modified Capabilities
None.

## Impact

- **Codebase / Scripts**: New module `backend/scripts/seed.py` and CLI launcher `scripts/seed.py`.
- **Infrastructure**: Enables automated database bootstrapping in Docker Compose and local developer environments.
- **Testing**: New integration test suite `backend/tests/test_seed_script.py` validating data creation, credential verification, and idempotency across repeated executions.
