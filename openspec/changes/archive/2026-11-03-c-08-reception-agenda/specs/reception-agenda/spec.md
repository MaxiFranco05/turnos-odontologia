# reception-agenda Specification

## Purpose

Provides a daily clinic-wide appointment agenda view for receptionists (`GET /api/agenda/dia`), with dentist filtering, eager loading of participant details, and lifecycle state tracking without exposing sensitive credentials.

## ADDED Requirements

### Requirement: Reception-Only Daily Agenda Query
The system SHALL provide an authenticated endpoint `GET /api/agenda/dia` accepting a required `fecha` query parameter (YYYY-MM-DD) and an optional `odontologo_id` filter, returning all scheduled appointments within the clinic day boundaries, accessible exclusively to users with the `recepcion` role (`RN-GL-01`, `RN-AU-02`).

#### Scenario: Successful daily agenda retrieval for all dentists (Expected Behavior)
- **WHEN** an authenticated `recepcion` user queries `GET /api/agenda/dia?fecha=2026-11-20`
- **THEN** the system returns HTTP `200 OK` with an array of appointments for all dentists on that date ordered by start time

#### Scenario: Filter daily agenda by specific dentist (Expected Behavior)
- **WHEN** an authenticated `recepcion` user queries `GET /api/agenda/dia?fecha=2026-11-20&odontologo_id=<dentist-id>`
- **THEN** the system returns HTTP `200 OK` containing only the appointments belonging to that dentist

#### Scenario: Unauthorized daily agenda query attempt by non-reception user (Business Error)
- **WHEN** an authenticated user with role `paciente` or `odontologo` requests `GET /api/agenda/dia?fecha=2026-11-20`
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-GL-01`)

#### Scenario: Daily agenda query with missing required date parameter (Business Error)
- **WHEN** an authenticated `recepcion` user requests `GET /api/agenda/dia` without the `fecha` parameter
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`

### Requirement: Dentist Validation and Error Handling on Filter
The system SHALL validate that any provided `odontologo_id` query parameter corresponds to an existing user whose role is `odontologo` (`CB-06`), rejecting nonexistent or non-dentist users.

#### Scenario: Querying daily agenda for a nonexistent dentist (Business Error CB-06)
- **WHEN** an authenticated `recepcion` user queries `GET /api/agenda/dia?fecha=2026-11-20&odontologo_id=999999`
- **THEN** the system responds with HTTP `404 Not Found`

#### Scenario: Querying daily agenda with an ID of a non-dentist user (Business Error CB-06)
- **WHEN** an authenticated `recepcion` user queries `GET /api/agenda/dia?fecha=2026-11-20&odontologo_id=<patient-id>` where the user exists but has role `paciente`
- **THEN** the system responds with HTTP `422 Unprocessable Entity`

### Requirement: Comprehensive Appointment Lifecycle Visibility and Patient Tracking
The system SHALL include appointments across all lifecycle states for the requested date, explicitly preserving patient cancellations (`cancelado`) and online booking origin (`origen=online`) to support operational tracking and attendance validation (`US-005 CA-1`, `CA-2`, `RN-TU-02`).

#### Scenario: Daily agenda includes patient cancellations and online booking origin (Edge Case)
- **WHEN** the daily agenda is requested for a date containing an appointment in state `cancelado` originated with `origen="online"`
- **THEN** the appointment is included in the response with `estado="cancelado"` and `origen="online"` allowing reception to track cancellations

#### Scenario: Daily agenda on a date with no appointments returns empty list (Edge Case)
- **WHEN** an authenticated `recepcion` user queries `GET /api/agenda/dia` for a valid date on which no appointments exist
- **THEN** the system responds with HTTP `200 OK` and an empty JSON list `[]`

### Requirement: Participant Information Projection and Credential Protection
The system SHALL project participant contact details (`nombre`, `nro_socio`, `email`) for both patient and dentist while strictly preventing the exposure of internal authentication secrets or credential flags (`password_hash`, `debe_cambiar_password`).

#### Scenario: Participant details are populated without exposing sensitive credentials (Expected Behavior)
- **WHEN** an appointment is returned in the daily agenda response
- **THEN** each item includes nested `paciente` and `odontologo` objects with public contact fields and strictly omits `password_hash` and `debe_cambiar_password`

#### Scenario: Response payload adheres to strict schema forbidding undeclared fields (Security Control)
- **WHEN** the daily agenda response is serialized
- **THEN** the output strictly matches the declared Pydantic schema with `extra="forbid"` without leaking extraneous internal attributes
