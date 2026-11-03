# Spec Delta: dentist-agenda

## MODIFIED Requirements

### Requirement: Role-Based Access Control and Password-Change Enforcement on Dentist Agenda
The system SHALL restrict `GET /api/mis-turnos` to authenticated users with role `odontologo` or `paciente` and `debe_cambiar_password=False`, rejecting unauthenticated requests with HTTP `401 Unauthorized` and `recepcion` role or pending password changes with HTTP `403 Forbidden` (`RN-AU-02`, `RN-GL-01`, `US-010`).

#### Scenario: Reject access by patient or reception role (Business Error)
- **WHEN** an authenticated `recepcion` user requests `GET /api/mis-turnos?fecha=2027-06-07`, or an authenticated `paciente` user requests the dentist-only query `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system rejects `recepcion` with HTTP `403 Forbidden` (`RN-GL-01`, `03_actores_y_roles.md`) and rejects the `paciente` dentist-parameter query with HTTP `422 Unprocessable Entity`

#### Scenario: Reject access when dentist has pending temporary password change (Business Error)
- **WHEN** an authenticated `odontologo` user with `debe_cambiar_password=True` requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system rejects the request with HTTP `403 Forbidden` and detail `"password_change_required"` (`US-010 CA-1`, `CA-2`)

#### Scenario: Reject unauthenticated access (Business Error)
- **WHEN** a client without a valid Bearer JWT requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system responds with HTTP `401 Unauthorized`
