# appointment-request Specification

## Purpose

Enables authenticated patients (`RolUsuario.PACIENTE`) to request online dental appointments (`POST /api/turnos`) in state `solicitado` (`origen="online"`), enforcing clinic timezone future-time rules (`RN-GL-02`), strict alignment with the dentist's schedule templates (`RN-AG-02`), and transactional server-side anti-overlap protection (`RN-AG-01`).

## ADDED Requirements

### Requirement: Patient-Only Online Appointment Request Creation
The system SHALL allow authenticated users with the `paciente` role and a completed password change (`debe_cambiar_password=False`) to create an appointment request via `POST /api/turnos`, binding `paciente_id` from the authenticated token and setting `estado="solicitado"` and `origen="online"` (`RN-TU-01`, `RN-GL-01`).

#### Scenario: Successful appointment request on a free template slot (Expected Behavior)
- **WHEN** authenticated synthetic patient Lucía Gómez (`rol="paciente"`, `debe_cambiar_password=False`) submits `POST /api/turnos` for synthetic dentist Dra. Sofía Martín (`rol="odontologo"`, Monday template `09:00:00–13:00:00`, `duracion_slot_minutos=30`) with `inicio` and `fin` matching the future Monday slot `09:30–10:00` in `America/Argentina/Buenos_Aires` and `motivo="Control anual y limpieza"`
- **THEN** the system persists the `Turno` record with `paciente_id` equal to Lucía Gómez's ID, `estado="solicitado"`, and `origen="online"`, and responds with HTTP `201 Created` containing the created appointment representation (`US-003 CA-1`, `CA-2`, `CA-3`)

#### Scenario: Unauthorized appointment request by reception or dentist role (Business Error)
- **WHEN** an authenticated user with role `recepcion` or `odontologo` submits `POST /api/turnos`
- **THEN** the system rejects the request with HTTP `403 Forbidden` without creating any appointment record (`RN-TU-01`, `RN-GL-01`, `RN-AU-02`)

#### Scenario: Blocked appointment request when mandatory password change is pending (Business Error)
- **WHEN** an authenticated `paciente` user with `debe_cambiar_password=True` submits `POST /api/turnos`
- **THEN** the system rejects the request with HTTP `403 Forbidden` and detail `"password_change_required"` (`US-010 CA-2`)

#### Scenario: Unauthenticated appointment request attempt (Business Error)
- **WHEN** a client without a valid Bearer JWT submits `POST /api/turnos`
- **THEN** the system rejects the request with HTTP `401 Unauthorized`

### Requirement: Dentist Existence and Role Validation
The system SHALL verify that the target `odontologo_id` in `POST /api/turnos` references an existing user whose role is `odontologo` (`CB-06`).

#### Scenario: Appointment request for a non-existent dentist ID (Business Error CB-06)
- **WHEN** an authenticated `paciente` user submits `POST /api/turnos` with an `odontologo_id` that does not exist in `usuarios`
- **THEN** the system rejects the request with HTTP `404 Not Found`

#### Scenario: Appointment request targeting a user whose role is not odontologo (Business Error CB-06)
- **WHEN** an authenticated `paciente` user submits `POST /api/turnos` where `odontologo_id` belongs to a user with role `paciente` or `recepcion`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`

### Requirement: Strict Schedule Template Slot Alignment
The system SHALL reject any appointment request whose `[inicio, fin)` interval in `America/Argentina/Buenos_Aires` does not match an exact, complete slot of `duracion_slot_minutos` derived from the target dentist's `PlantillaDisponibilidad` for that weekday (`RN-AG-02`, `CB-02`).

#### Scenario: Reject appointment request outside dentist availability template hours (Business Error)
- **WHEN** synthetic dentist Dra. Sofía Martín only has a Monday template from `09:00:00` to `13:00:00` (`duracion_slot_minutos=30`) and an authenticated `paciente` requests `POST /api/turnos` on a future Monday from `15:00` to `15:30` (or on a Tuesday with no template)
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (`RN-AG-02`)

#### Scenario: Reject appointment request with unaligned boundaries or invalid slot duration (Edge Case CB-02)
- **WHEN** synthetic dentist Dra. Sofía Martín has a Monday template from `09:00:00` to `10:00:00` with `duracion_slot_minutos=40` and an authenticated `paciente` requests `09:40–10:00` (incomplete 20-minute remainder), `09:10–09:50` (misaligned start), or `09:00–10:00` (wrong duration)
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` because only the complete grid slot `09:00–09:40` is bookable (`RN-AG-02`, `CB-02`)

### Requirement: Future Timestamp Enforcement in Clinic Timezone
The system SHALL reject any appointment request whose start timestamp `inicio` is in the past or less than or equal to the current clinic timestamp in `TIMEZONE` (`America/Argentina/Buenos_Aires`) (`RN-GL-02`, `CB-05`).

#### Scenario: Reject appointment request on a past date (Business Error)
- **WHEN** an authenticated `paciente` user submits `POST /api/turnos` for a date prior to today in `America/Argentina/Buenos_Aires`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (`RN-GL-02`)

#### Scenario: Reject appointment request for an already elapsed slot on the current day (Edge Case CB-05)
- **WHEN** the clinic clock in `America/Argentina/Buenos_Aires` is `10:15` on a Monday and an authenticated `paciente` submits `POST /api/turnos` for today's slot `10:00–10:30` or `09:30–10:00`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` because `inicio <= now_local` (`RN-GL-02`, `CB-05`)

### Requirement: Transactional Dentist Schedule Non-Overlap Invariant
The system SHALL guarantee within a transactional boundary (`SELECT ... FOR UPDATE` plus database integrity enforcement) that no new appointment overlaps in `[inicio, fin)` with an existing active appointment (`solicitado`, `confirmado`, `presente`, `ausente`) of the same dentist (`RN-AG-01`, `US-009`).

#### Scenario: Reject appointment request overlapping an active appointment (Business Error CB-04)
- **WHEN** synthetic dentist Dra. Sofía Martín already has an appointment in state `solicitado`, `confirmado`, `presente`, or `ausente` intersecting `[09:30, 10:00)` on a future Monday and an authenticated `paciente` submits `POST /api/turnos` for `[09:30, 10:00)`
- **THEN** the system rejects the request with HTTP `409 Conflict` and leaves the database state unchanged (`RN-AG-01`, `US-003 CA-3`, `US-009`)

#### Scenario: Allow appointment request on a slot released by a cancelled or annulled appointment (Edge Case CB-03)
- **WHEN** synthetic dentist Dra. Sofía Martín has a previous appointment on future Monday `[09:30, 10:00)` in state `cancelado` or `anulado` (`RN-TU-04`) and an authenticated `paciente` submits `POST /api/turnos` for `[09:30, 10:00)`
- **THEN** the system accepts the reservation and responds with HTTP `201 Created` (`CB-03`)

#### Scenario: Allow contiguous back-to-back appointment requests without false overlap (Edge Case CB-01)
- **WHEN** synthetic dentist Dra. Sofía Martín has an active appointment on future Monday `[09:00, 09:30)` and an authenticated `paciente` submits `POST /api/turnos` for the immediately adjacent slot `[09:30, 10:00)` (`fin_A == inicio_B`)
- **THEN** the system accepts the reservation and responds with HTTP `201 Created` because half-open intervals `[09:00, 09:30)` and `[09:30, 10:00)` do not intersect (`CB-01`)

### Requirement: Strict Payload Validation and Anti-Overposting
The system SHALL validate `POST /api/turnos` request bodies strictly, rejecting undeclared fields (`extra="forbid"`), empty or whitespace-only `motivo`, or chronological inversions (`fin <= inicio`) with HTTP `422 Unprocessable Entity`.

#### Scenario: Reject payload with undeclared fields or BOLA attempt (Business Error)
- **WHEN** an authenticated `paciente` submits `POST /api/turnos` including undeclared properties such as `"paciente_id": 999`, `"estado": "confirmado"`, or `"origen": "manual"`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (`extra="forbid"`)

#### Scenario: Reject payload with empty motivo or inverted timestamps (Business Error)
- **WHEN** an authenticated `paciente` submits `POST /api/turnos` with `motivo="   "` (empty after strip) or with `fin <= inicio`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`
