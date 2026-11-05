# Tasks: C-16 — Database Seed Data Script (`c-16-seed-data-script`)

## 1. Core Seeding Engine & Data Models

- [x] 1.1 Implement async seeding engine in `backend/app/infrastructure/seed.py` with function `seed_data(session: AsyncSession, reset: bool = False, base_date: datetime.date | None = None) -> dict[str, int]`, creating synthetic accounts (reception with `debe_cambiar_password=True`, 2 dentists, 2 patients), recurring weekday availability templates, and demonstration appointments using SQLAlchemy 2.0 `select()` lookups to guarantee strict idempotency. Verify with a focused programmatic test.

## 2. CLI Scripts & Execution Wrappers

- [x] 2.1 Create CLI executable runners at `backend/scripts/seed.py` and root wrapper `scripts/seed.py` that parse command-line flags (`--reset`), initialize database connection via `init_engine` / `init_session_factory`, run `seed_data`, and output formatted summary logs. Verify by running `python scripts/seed.py --help`.

## 3. Automated Tests & Acceptance Verification

- [x] 3.1 Implement comprehensive test suite in `backend/tests/test_seed_script.py` testing initial seed creation, reception security flags (`debe_cambiar_password=True`), template availability rules (`RN-AG-01`), demo appointment state machine validity, and strict idempotency across multiple consecutive executions without mocks against a real SQLite database. Verify by executing `pytest backend/tests/test_seed_script.py` and ensuring all tests pass.

## Workflow follow-up

- Validate all planning artifacts with `openspec validate c-16-seed-data-script --strict`.
- Audit planning artifacts with independent subagent.
- Proceed to `/opsx:apply c-16-seed-data-script` under Strict TDD Mode.
