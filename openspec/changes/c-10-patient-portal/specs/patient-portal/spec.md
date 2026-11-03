# patient-portal Specification

## Purpose

Provides the self-appointment listing endpoint (`GET /api/mis-turnos?fecha_desde=&fecha_hasta=`) for authenticated `paciente` users (`US-004`, `Flujo 5`), enforcing strict server-side ownership isolation (`paciente_id == current_user.id`, `RN-GL-01`), optional inclusive clinic-timezone date filtering (`America/Argentina/Buenos_Aires`), chronological ordering by `inicio`, and nested non-sensitive dentist identification.

## ADDED Requirements

### Requirement: Patient Self-Appointment Listing Scoped to Authenticated Patient
The system SHALL allow an authenticated `paciente` user (`debe_cambiar_password=False`) to query `GET /api/mis-turnos` with optional `fecha_desde` and `fecha_hasta` (`YYYY-MM-DD`) and SHALL return only the appointments belonging to that patient (`turno.paciente_id == current_user.id`), ordered ascending by `inicio`, across all lifecycle states, including a nested `odontologo` summary (`id`, `nombre`, `nro_socio`, `email`) (`US-004`, `Flujo 5`, `RN-GL-01`).

#### Scenario: Patient retrieves all own appointments without date filters ordered chronologically (Expected Behavior)
- **WHEN** authenticated synthetic patient Lucía Gómez (`rol="paciente"`, `debe_cambiar_password=False`) requests `GET /api/mis-turnos` without query parameters
- **THEN** the system responds with HTTP `200 OK` and a JSON list containing all of Lucía Gómez's past and future appointments across all lifecycle states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`), sorted ascending by `inicio`, where each item includes `id`, `paciente_id`, `odontologo_id`, `inicio`, `fin`, `motivo`, `estado`, `origen`, and `odontologo` (`id`, `nombre`, `nro_socio`, `email`) without exposing `password_hash` (`Flujo 5`)

#### Scenario: Patient filters own appointments by inclusive fecha_desde and fecha_hasta range (Expected Behavior)
- **WHEN** authenticated synthetic patient Lucía Gómez requests `GET /api/mis-turnos?fecha_desde=2027-06-07&fecha_hasta=2027-06-14`
- **THEN** the system responds with HTTP `200 OK` returning only her appointments falling within `[2027-06-07 00:00:00, 2027-06-15 00:00:00)` in `America/Argentina/Buenos_Aires` and excluding appointments before `2027-06-07` or after `2027-06-14`

#### Scenario: Patient never sees appointments belonging to another patient (Edge Case — BOLA Isolation)
- **WHEN** synthetic patients Lucía Gómez and Martín Pérez both have appointments in the same date range and Lucía Gómez requests `GET /api/mis-turnos`
- **THEN** the response includes only Lucía Gómez's appointments (`paciente_id == current_user.id`) and omits all appointments belonging to Martín Pérez (`RN-GL-01`, `US-004 CA-1`)

#### Scenario: Patient cancels a listed appointment with 24h+ notice and sees updated state in mis-turnos (Expected Behavior — Flujo 5 E2E)
- **WHEN** synthetic patient Lucía Gómez lists her future appointments via `GET /api/mis-turnos`, cancels one with `>= 24h` anticipation via `PATCH /api/turnos/{id}` (`{"estado": "cancelado"}`), and queries `GET /api/mis-turnos` again
- **THEN** the appointment appears with `estado="cancelado"` in `GET /api/mis-turnos` and its slot is released in `GET /api/disponibilidad` (`CB-03`, `US-004 CA-1..3`)

### Requirement: Date Range and Parameter Validation for Patient Portal Queries
The system SHALL reject with HTTP `422 Unprocessable Entity` any `GET /api/mis-turnos` request by a `paciente` where `fecha_hasta < fecha_desde`, where dates are malformed, or where the dentist-only `fecha` query parameter is supplied.

#### Scenario: Reject inverted date range where fecha_hasta is earlier than fecha_desde (Business Error)
- **WHEN** an authenticated `paciente` user requests `GET /api/mis-turnos?fecha_desde=2027-06-14&fecha_hasta=2027-06-07`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`

#### Scenario: Reject dentist-only fecha parameter when called by a patient (Edge Case)
- **WHEN** an authenticated `paciente` user requests `GET /api/mis-turnos?fecha=2027-06-07`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`
