# dentist-agenda Specification

## Purpose

Provides the daily self-agenda query endpoint (`GET /api/mis-turnos?fecha=YYYY-MM-DD`) for authenticated `odontologo` users (`US-007`, `Flujo 4`), enforcing strict server-side ownership isolation (`odontologo_id == current_user.id`, `RN-AU-02`, `RN-GL-01`), clinic timezone day boundaries (`America/Argentina/Buenos_Aires`), chronological ordering by `inicio`, and nested non-sensitive patient identification.

## ADDED Requirements

### Requirement: Dentist Daily Self-Agenda Listing Scoped to Authenticated Dentist
The system SHALL allow an authenticated `odontologo` user (`debe_cambiar_password=False`) to query `GET /api/mis-turnos?fecha=YYYY-MM-DD` and SHALL return only the appointments assigned to that dentist (`turno.odontologo_id == current_user.id`) for `fecha` in `America/Argentina/Buenos_Aires`, ordered ascending by `inicio`, across all lifecycle states, including a nested `paciente` summary (`id`, `nombre`, `nro_socio`, `email`) (`US-007`, `RN-AU-02`).

#### Scenario: Dentist retrieves own daily appointments ordered chronologically with patient summary (Expected Behavior)
- **WHEN** authenticated synthetic dentist Dra. Sofía Martín (`rol="odontologo"`, `debe_cambiar_password=False`) requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system responds with HTTP `200 OK` and a JSON list containing only Dra. Sofía Martín's appointments on `2027-06-07` in `America/Argentina/Buenos_Aires` across all states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`), sorted ascending by `inicio`, where each item includes `id`, `paciente_id`, `odontologo_id`, `inicio`, `fin`, `motivo`, `estado`, `origen`, and `paciente` (`id`, `nombre`, `nro_socio`, `email`) without exposing `password_hash` (`US-007 CA-1`, `Flujo 4`)

#### Scenario: Dentist never sees appointments belonging to another dentist (Edge Case — BOLA Isolation)
- **WHEN** synthetic dentists Dra. Sofía Martín and Dr. Juan Pérez both have appointments on `2027-06-07` and Dra. Sofía Martín requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the response includes only Dra. Sofía Martín's appointments (`odontologo_id == current_user.id`) and omits all appointments assigned to Dr. Juan Pérez (`US-007 CA-1`, `RN-AU-02`)

#### Scenario: Dentist receives empty list when no appointments exist on the requested date (Edge Case)
- **WHEN** authenticated synthetic dentist Dra. Sofía Martín requests `GET /api/mis-turnos?fecha=2027-06-08` and has no appointments on that date
- **THEN** the system responds with HTTP `200 OK` and an empty JSON array `[]`

#### Scenario: Adjacent appointments on the same day are returned in ascending order without overlap distortion (Edge Case CB-01)
- **WHEN** Dra. Sofía Martín has contiguous appointments `09:00–09:30` and `09:30–10:00` (`fin_A == inicio_B`) on `2027-06-07` and requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system returns both appointments in exact chronological order (`09:00`, then `09:30`) and excludes appointments from `2027-06-06` or `2027-06-08` (`CB-01`)

### Requirement: Role-Based Access Control and Password-Change Enforcement on Dentist Agenda
The system SHALL restrict `GET /api/mis-turnos?fecha=YYYY-MM-DD` (in `C-09`) to authenticated users with role `odontologo` and `debe_cambiar_password=False`, rejecting unauthenticated requests with HTTP `401 Unauthorized` and unauthorized roles or pending password changes with HTTP `403 Forbidden` (`RN-AU-02`, `RN-GL-01`, `US-010`).

#### Scenario: Reject access by patient or reception role (Business Error)
- **WHEN** an authenticated `paciente` or `recepcion` user requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-GL-01`, `03_actores_y_roles.md`)

#### Scenario: Reject access when dentist has pending temporary password change (Business Error)
- **WHEN** an authenticated `odontologo` user with `debe_cambiar_password=True` requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system rejects the request with HTTP `403 Forbidden` and detail `"password_change_required"` (`US-010 CA-1`, `CA-2`)

#### Scenario: Reject unauthenticated access (Business Error)
- **WHEN** a client without a valid Bearer JWT requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system responds with HTTP `401 Unauthorized`

### Requirement: Date Query Parameter Validation
The system SHALL require a valid ISO 8601 date (`YYYY-MM-DD`) in the `fecha` query parameter on `GET /api/mis-turnos` for dentist daily agenda queries, returning HTTP `422 Unprocessable Entity` when `fecha` is missing or malformed.

#### Scenario: Reject missing or malformed fecha query parameter (Business Error)
- **WHEN** an authenticated `odontologo` user requests `GET /api/mis-turnos` without `fecha` or with `fecha=fecha-invalida`
- **THEN** the system responds with HTTP `422 Unprocessable Entity`
