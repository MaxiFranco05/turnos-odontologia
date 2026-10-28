# appointment-integrity Specification

## Purpose

Enforces relational and domain invariants governing appointment time ordering and schedule exclusivity to prevent double-booking per professional.

## Requirements

### Requirement: Chronological appointment time ordering
The system SHALL reject any appointment reservation whose conclusion timestamp is not strictly greater than its commencement timestamp.

#### Scenario: Valid chronological bounds
- **WHEN** an appointment is registered with end timestamp strictly after start timestamp
- **THEN** the record passes chronological validation

#### Scenario: Invalid inverted or identical timestamps
- **WHEN** an appointment is registered with end timestamp prior to or identical to its start timestamp
- **THEN** the database or domain layer rejects the operation with an integrity violation

### Requirement: Dentist appointment non-collision invariant
The system SHALL guarantee that an active appointment cannot overlap in time with another non-cancelled and non-annulled appointment for the same dentist.

#### Scenario: Non-overlapping consecutive appointments
- **WHEN** a new appointment is created for a dentist starting at or after an existing appointment's end timestamp
- **THEN** the reservation is accepted without conflict

#### Scenario: Overlapping appointment for the same dentist
- **WHEN** a new appointment for a dentist coincides with or intersects the time interval of an existing active appointment
- **THEN** the system rejects the creation, preserving schedule non-collision (RN-AG-01)

#### Scenario: Overlapping allowed when previous appointment is cancelled or annulled
- **WHEN** a new appointment overlaps with an appointment that is marked with state `cancelado` or `anulado`
- **THEN** the reservation is accepted because the time slot was released
