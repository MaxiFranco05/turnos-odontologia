# seed-data-script Specification

## Purpose

Provides automated, idempotent database provisioning of clinic accounts (reception, dentists, patients), recurring weekly availability templates, and demonstration appointments for local development, automated testing, and production deployment.

## ADDED Requirements

### Requirement: Multi-Role Account Seeding with Bcrypt Credentials
The system SHALL provision administrative, professional, and patient demonstration accounts with valid bcrypt-hashed passwords and appropriate role assignments, guaranteeing unique identifiers and initial profile flags (`RN-AU-01`).

#### Scenario: Initial execution seeds all required multi-role accounts (Expected Behavior)
- **WHEN** the seed script executes against an empty or existing database
- **THEN** accounts for `recepcion`, `odontologo`, and `paciente` roles are present with valid bcrypt password hashes and verified identifiers

#### Scenario: Receptionist account requires password change upon initial login (Security Control)
- **WHEN** the default receptionist account is created by the seed script
- **THEN** the account has `debe_cambiar_password=True` and `perfil_completo=True` enforcing mandatory credential rotation upon first login

### Requirement: Recurring Weekly Availability Templates Seeding
The system SHALL provision weekly recurring availability templates (`PlantillaDisponibilidad`) for each dentist across standard working days (Monday to Friday) in morning and afternoon windows without interval overlaps (`RN-AG-01`).

#### Scenario: Templates are created for standard morning and afternoon shifts (Expected Behavior)
- **WHEN** the seed script completes execution
- **THEN** each seeded dentist has active availability templates for weekdays with 30-minute slot durations and specified specialties

#### Scenario: Availability templates strictly adhere to interval ordering (Integrity Rule)
- **WHEN** availability templates are created
- **THEN** all records satisfy `hora_fin > hora_inicio`, `duracion_slot_minutos > 0`, and non-overlapping time slots per dentist

### Requirement: Non-Overlapping Demonstration Appointments Seeding
The system SHALL seed realistic demonstration appointments across varied lifecycle states (`solicitado`, `confirmado`, `cancelado`) ensuring zero schedule overlap on dentist calendars (Hard Rule #13).

#### Scenario: Demonstration appointments are populated with valid lifecycle states (Expected Behavior)
- **WHEN** demonstration appointments are seeded
- **THEN** each appointment links a valid patient and dentist, contains valid timestamps, and adheres to the state machine rules without slot collision

### Requirement: Strictly Idempotent Seeding Execution
The seeding routine SHALL be safe to execute multiple times against the same database without creating duplicate users, violating unique constraints, or failing with database errors.

#### Scenario: Repeated execution does not duplicate records or cause errors (Idempotency)
- **WHEN** the seed script is executed consecutively two or more times against the same database
- **THEN** the total count of accounts, templates, and appointments remains identical and the script exits successfully with code 0

#### Scenario: Optional reset flag cleanly purges and regenerates data when requested (Admin Control)
- **WHEN** the seed script is executed with `--reset` or programmatic `reset=True`
- **THEN** the target entities are refreshed cleanly and recreated with baseline demonstration data
