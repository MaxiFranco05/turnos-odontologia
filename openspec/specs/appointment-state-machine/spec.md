# appointment-state-machine Specification

## Purpose

Governs server-side lifecycle transitions of dental appointments (`PATCH /api/turnos/{id}`) across the `paciente`, `recepcion`, and `odontologo` roles (`DD-03`, `RN-TU-01..04`), enforcing role authorization (`RN-GL-01`), resource ownership (`RN-AU-02`), and minimum cancellation/annulment anticipation (`RN-TU-05`, `CANCEL_MIN_HOURS=24`) in the clinic timezone.

## Requirements

### Requirement: Patient Self-Service Cancellation with 24-Hour Minimum Anticipation
The system SHALL allow an authenticated `paciente` user (`debe_cambiar_password=False`) to transition only their own appointment (`turno.paciente_id == current_user.id`) from `solicitado` or `confirmado` to `cancelado` via `PATCH /api/turnos/{id}` when at least `CANCEL_MIN_HOURS` (default `24` hours) remain before `turno.inicio` in `America/Argentina/Buenos_Aires` (`RN-TU-01`, `RN-TU-04`, `RN-TU-05`, `US-004`).

#### Scenario: Successful cancellation of own requested or confirmed appointment with 24h+ notice (Expected Behavior)
- **WHEN** authenticated synthetic patient Lucía Gómez (`rol="paciente"`) submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado"}` for her own appointment in state `solicitado` or `confirmado` whose `inicio` is at least `24` hours in the future in `America/Argentina/Buenos_Aires`
- **THEN** the system updates `turno.estado` to `"cancelado"`, releases the time slot for new bookings (`CB-03`), and responds with HTTP `200 OK` containing the updated appointment (`US-004 CA-1`, `CA-2`, `CA-3`)

#### Scenario: Reject patient cancellation within less than 24 hours of appointment start (Business Error)
- **WHEN** authenticated synthetic patient Lucía Gómez submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado"}` for her own appointment whose `inicio` is less than `24` hours away (or in the past) in `America/Argentina/Buenos_Aires`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` and leaves the appointment state unchanged (`RN-TU-05`, `RN-GL-02`)

#### Scenario: Exact 24-hour boundary allows patient cancellation (Edge Case)
- **WHEN** authenticated synthetic patient Lucía Gómez submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado"}` when `turno.inicio - now_local` equals exactly `24` hours (`timedelta(hours=24)`)
- **THEN** the system accepts the transition and responds with HTTP `200 OK` (`RN-TU-05`)

#### Scenario: Reject patient attempt to cancel another patient's appointment (Business Error)
- **WHEN** authenticated synthetic patient Martín Pérez submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado"}` for an appointment belonging to synthetic patient Lucía Gómez (`turno.paciente_id != current_user.id`)
- **THEN** the system rejects the request with HTTP `403 Forbidden` without modifying the appointment (`RN-GL-01`, `US-004 CA-1`)

#### Scenario: Reject patient attempt to transition to non-patient target states (Business Error)
- **WHEN** an authenticated `paciente` user submits `PATCH /api/turnos/{id}` with `{"estado": "confirmado"}`, `{"estado": "anulado"}`, `{"estado": "presente"}`, or `{"estado": "ausente"}`
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-TU-01`, `RN-GL-01`)

### Requirement: Reception Confirmation and Annulment Transitions
The system SHALL allow an authenticated `recepcion` user (`debe_cambiar_password=False`) to transition any future `solicitado` appointment to `confirmado`, and any `solicitado` or `confirmado` appointment to `anulado` via `PATCH /api/turnos/{id}` when at least `CANCEL_MIN_HOURS` (`24` hours) remain before `turno.inicio` (`RN-TU-02`, `RN-TU-04`, `RN-TU-05`, `US-006`).

#### Scenario: Successful confirmation of a requested appointment by reception (Expected Behavior)
- **WHEN** an authenticated `recepcion` user submits `PATCH /api/turnos/{id}` with `{"estado": "confirmado"}` for a future appointment currently in state `solicitado`
- **THEN** the system updates `turno.estado` to `"confirmado"` and responds with HTTP `200 OK` (`US-006 CA-1`, `RN-TU-02`)

#### Scenario: Successful annulment of a requested or confirmed appointment by reception with 24h+ notice (Expected Behavior)
- **WHEN** an authenticated `recepcion` user submits `PATCH /api/turnos/{id}` with `{"estado": "anulado"}` for an appointment in state `solicitado` or `confirmado` whose `inicio` is at least `24` hours in the future in `America/Argentina/Buenos_Aires`
- **THEN** the system updates `turno.estado` to `"anulado"`, releases the time slot (`CB-03`), and responds with HTTP `200 OK` (`US-006 CA-2`, `RN-TU-02`, `RN-TU-04`)

#### Scenario: Reject reception annulment within less than 24 hours of appointment start (Business Error)
- **WHEN** an authenticated `recepcion` user submits `PATCH /api/turnos/{id}` with `{"estado": "anulado"}` for an appointment whose `inicio` is less than `24` hours away in `America/Argentina/Buenos_Aires`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` and leaves the appointment unchanged (`RN-TU-05`)

#### Scenario: Reject reception attempt to set patient or dentist states (Business Error)
- **WHEN** an authenticated `recepcion` user submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado"}`, `{"estado": "presente"}`, or `{"estado": "ausente"}`
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-TU-02`, `RN-TU-04`, `RN-GL-01`)

### Requirement: Dentist Attendance Marking on Own Confirmed Appointments
The system SHALL allow an authenticated `odontologo` user (`debe_cambiar_password=False`) to transition only their own appointments (`turno.odontologo_id == current_user.id`) from `confirmado` to `presente` or `ausente` via `PATCH /api/turnos/{id}` (`RN-TU-03`, `RN-AU-02`, `US-008`).

#### Scenario: Successful marking of present or absent by assigned dentist (Expected Behavior)
- **WHEN** synthetic dentist Dra. Sofía Martín (`rol="odontologo"`) submits `PATCH /api/turnos/{id}` with `{"estado": "presente"}` or `{"estado": "ausente"}` for an appointment assigned to her (`turno.odontologo_id == current_user.id`) currently in state `confirmado`
- **THEN** the system updates `turno.estado` accordingly and responds with HTTP `200 OK` (`US-008 CA-1`, `CA-2`)

#### Scenario: Reject dentist attempt to modify another dentist's appointment (Business Error)
- **WHEN** synthetic dentist Dr. Juan Pérez (`rol="odontologo"`) submits `PATCH /api/turnos/{id}` with `{"estado": "presente"}` or `{"estado": "ausente"}` for an appointment assigned to Dra. Sofía Martín (`turno.odontologo_id != current_user.id`)
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-AU-02`, `RN-GL-01`, `US-008 CA-1`)

#### Scenario: Reject dentist attempt to confirm, annul, or cancel an appointment (Business Error)
- **WHEN** an authenticated `odontologo` user submits `PATCH /api/turnos/{id}` with `{"estado": "confirmado"}`, `{"estado": "anulado"}`, or `{"estado": "cancelado"}`
- **THEN** the system rejects the request with HTTP `403 Forbidden` (`RN-TU-03`, `RN-GL-01`)

### Requirement: Invalid Source-State Conflict and Non-Existent Appointment Handling
The system SHALL reject with HTTP `409 Conflict` any transition where the role is authorized for the target state in general, but the appointment's current `estado` does not allow that transition (e.g., transitioning from a terminal state `cancelado`, `anulado`, `presente`, `ausente`, or marking `presente`/`ausente` on an unconfirmed `solicitado` appointment), and SHALL return HTTP `404 Not Found` when `{id}` does not exist.

#### Scenario: Reject transition from a terminal state or unconfirmed attendance marking (Business Error)
- **WHEN** `recepcion` attempts `{"estado": "confirmado"}` on an already `confirmado`, `cancelado`, or `anulado` appointment, OR `odontologo` attempts `{"estado": "presente"}` on a `solicitado` appointment, OR `paciente` attempts `{"estado": "cancelado"}` on an already `cancelado`, `anulado`, `presente`, or `ausente` appointment
- **THEN** the system rejects the request with HTTP `409 Conflict` and leaves `turno.estado` unchanged (`US-008 CA-2`, `Flujo 3`)

#### Scenario: Reject transition on a non-existent appointment ID (Business Error)
- **WHEN** an authenticated user submits `PATCH /api/turnos/999999` for an appointment ID that does not exist
- **THEN** the system responds with HTTP `404 Not Found`

### Requirement: Slot Liberation Upon Cancellation or Annulment
The system SHALL immediately release the time slot of any appointment transitioned to `cancelado` or `anulado` so that `GET /api/disponibilidad` lists the slot as free and `POST /api/turnos` accepts a new reservation for that interval (`CB-03`, `RN-TU-04`).

#### Scenario: Cancelled or annulled appointment slot becomes bookable again (Edge Case CB-03)
- **WHEN** an appointment on a future template slot is transitioned via `PATCH /api/turnos/{id}` to `cancelado` (by its patient) or `anulado` (by reception)
- **THEN** subsequent calls to `GET /api/disponibilidad` include that slot as available and `POST /api/turnos` allows booking a new `solicitado` appointment in that same `[inicio, fin)` interval (`CB-03`, `RN-TU-04`)

### Requirement: Strict Input Validation on State Transition Payloads
The system SHALL validate `PATCH /api/turnos/{id}` payloads with `ConfigDict(extra="forbid")`, rejecting undeclared fields or invalid `EstadoTurno` values with HTTP `422 Unprocessable Entity` (Hard Rule #1).

#### Scenario: Reject PATCH payload with undeclared fields or invalid state value (Business Error)
- **WHEN** an authenticated user submits `PATCH /api/turnos/{id}` with `{"estado": "cancelado", "motivo": "cambio"}` or `{"estado": "reprogramado"}`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (`extra="forbid"`)
