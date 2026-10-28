# Spec Delta: core-data-models

## Purpose

Defines the relational data models and persistence schemas for user accounts, availability templates, and appointment records with role-based attributes and database-level integrity constraints.

## ADDED Requirements

### Requirement: User model representation and credential constraints
The system SHALL persist user accounts with role discrimination, hashed credentials, and require at least one valid identifier between email and socio number.

#### Scenario: User creation with valid credentials
- **WHEN** a user account is created with either an email or a socio number and a hashed password
- **THEN** the record is stored in the database with timestamps and default security flags (`debe_cambiar_password`, `perfil_completo`)

#### Scenario: User creation without any identifier
- **WHEN** a user account is submitted without an email and without a socio number
- **THEN** persistence fails with an integrity constraint violation

### Requirement: Availability template representation
The system SHALL persist weekly availability templates associated with dentists defining valid time intervals and slot durations.

#### Scenario: Valid availability template creation
- **WHEN** a template is stored with an associated dentist, a day of week (0 to 6), a start time earlier than end time, and a positive slot duration
- **THEN** the record is persisted successfully

#### Scenario: Inverted time range in template
- **WHEN** an availability template is submitted where start time is greater than or equal to end time
- **THEN** persistence is rejected by a database check constraint

### Requirement: Appointment model representation
The system SHALL store appointment reservations with patient and dentist references, timestamps, origin, and an explicit lifecycle state.

#### Scenario: Valid appointment creation
- **WHEN** an appointment is scheduled with valid patient and dentist foreign keys, a valid time range, and an initial state
- **THEN** the appointment is persisted with tracking timestamps and indexed for querying
