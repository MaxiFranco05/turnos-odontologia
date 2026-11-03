# availability-engine Specification

## Purpose

Provides administrative management of weekly dentist schedule templates (`PlantillaDisponibilidad`) with server-side non-overlap validation (`RN-AG-01`) and real-time calculation of bookable appointment slots (`GET /api/disponibilidad`) derived from templates minus active appointments (`RN-AG-02`, `RN-GL-02`).

## Requirements

### Requirement: Reception-Only Availability Template Creation and Listing
The system SHALL allow authenticated users with the `recepcion` role to create (`POST /api/plantillas`) and list (`GET /api/plantillas`) weekly availability templates for users with the `odontologo` role, rejecting other roles with HTTP `403 Forbidden` (`RN-GL-01`).

#### Scenario: Successful template creation by reception (Expected Behavior)
- **WHEN** an authenticated `recepcion` user submits `POST /api/plantillas` for synthetic dentist Dra. Sofía Martín (`rol="odontologo"`) with `dia_semana=0`, `hora_inicio="09:00:00"`, `hora_fin="13:00:00"`, `duracion_slot_minutos=30`, and `prestacion="Consulta general"`
- **THEN** the system persists the template and responds with HTTP `201 Created` containing the created template representation with its generated `id`

#### Scenario: Listing templates filtered by dentist (Expected Behavior)
- **WHEN** an authenticated `recepcion` user requests `GET /api/plantillas?odontologo_id=<id>`
- **THEN** the system responds with HTTP `200 OK` returning only the templates belonging to that dentist ordered by `dia_semana` and `hora_inicio`

#### Scenario: Unauthorized template creation attempt by patient or dentist (Business Error)
- **WHEN** an authenticated user with role `paciente` or `odontologo` submits `POST /api/plantillas`, `PATCH /api/plantillas/{id}`, or `DELETE /api/plantillas/{id}`
- **THEN** the system rejects the request with HTTP `403 Forbidden` without modifying any template records (`RN-GL-01`, `RN-AU-02`)

#### Scenario: Template creation for non-dentist or non-existent user (Business Error)
- **WHEN** an authenticated `recepcion` user submits `POST /api/plantillas` with an `odontologo_id` that does not exist or belongs to a user whose `rol` is not `odontologo`
- **THEN** the system rejects the request with HTTP `404 Not Found` (if user does not exist) or HTTP `422 Unprocessable Entity` (if user is not a dentist)

### Requirement: Same-Day Template Non-Overlap Invariant
The system SHALL reject any creation or partial update of an availability template whose `[hora_inicio, hora_fin)` interval intersects an existing template for the same dentist on the same `dia_semana` (`RN-AG-01`).

#### Scenario: Overlapping template on the same day for the same dentist (Business Error)
- **WHEN** synthetic dentist Dra. Sofía Martín already has a template on `dia_semana=0` from `09:00:00` to `13:00:00` and `recepcion` submits a template on `dia_semana=0` from `12:00:00` to `15:00:00`
- **THEN** the system rejects the operation with HTTP `409 Conflict` indicating a schedule template overlap (`RN-AG-01`)

#### Scenario: Contiguous adjacent templates on the same day are allowed (Edge Case CB-01)
- **WHEN** synthetic dentist Dra. Sofía Martín has a template on `dia_semana=0` from `09:00:00` to `11:00:00` and `recepcion` creates a second template on `dia_semana=0` from `11:00:00` to `13:00:00`
- **THEN** the system accepts and persists the second template with HTTP `201 Created` because half-open intervals `[09:00, 11:00)` and `[11:00, 13:00)` do not overlap

### Requirement: Partial Template Update via PATCH and Deletion
The system SHALL support partial updates to availability templates via `PATCH /api/plantillas/{id}` applying only client-supplied fields and re-validating chronological ordering and non-overlap on the merged state, as well as template removal via `DELETE /api/plantillas/{id}`.

#### Scenario: Partial update of template end time and slot duration (Expected Behavior)
- **WHEN** an authenticated `recepcion` user sends `PATCH /api/plantillas/{id}` with `{"hora_fin": "12:00:00", "duracion_slot_minutos": 20}` for an existing `09:00:00–13:00:00` template
- **THEN** the system merges the supplied fields with the stored template, verifies `hora_fin > hora_inicio` and non-overlap, persists the change, and responds with HTTP `200 OK`

#### Scenario: Partial update resulting in inverted time range against stored start time (Edge Case)
- **WHEN** an existing template has `hora_inicio="09:00:00"` and `hora_fin="13:00:00"`, and `recepcion` sends `PATCH /api/plantillas/{id}` with only `{"hora_fin": "08:30:00"}`
- **THEN** the system rejects the update with HTTP `422 Unprocessable Entity` because the merged `hora_fin` is not greater than the stored `hora_inicio`

#### Scenario: Template deletion by reception (Expected Behavior)
- **WHEN** an authenticated `recepcion` user sends `DELETE /api/plantillas/{id}` for an existing template
- **THEN** the system deletes the template record and responds with HTTP `204 No Content`

#### Scenario: Partial update that introduces an overlap is rejected (Business Error)
- **WHEN** synthetic dentist Dra. Sofía Martín has templates on `dia_semana=0` from `09:00:00` to `11:00:00` and from `14:00:00` to `16:00:00`, and `recepcion` sends `PATCH` on the first template with `{"hora_fin": "15:00:00"}`
- **THEN** the system rejects the update with HTTP `409 Conflict` and leaves both templates unchanged (`RN-AG-01`)

#### Scenario: Update or deletion of a non-existent template (Business Error)
- **WHEN** an authenticated `recepcion` user sends `PATCH /api/plantillas/{id}` or `DELETE /api/plantillas/{id}` with an `id` that does not exist
- **THEN** the system responds with HTTP `404 Not Found`

#### Scenario: Empty partial update payload is an idempotent no-op (Edge Case)
- **WHEN** an authenticated `recepcion` user sends `PATCH /api/plantillas/{id}` with an empty JSON object `{}`
- **THEN** the system performs no modification and responds with HTTP `200 OK` returning the unchanged template (JSON Merge Patch semantics, RFC 7396)

### Requirement: Strict Input Validation on Template Payloads
The system SHALL validate template payloads strictly, rejecting undeclared fields (`extra="forbid"`), invalid `dia_semana` values outside `0..6`, non-positive `duracion_slot_minutos`, or `hora_fin <= hora_inicio`.

#### Scenario: Reject payload containing undeclared fields (Business Error)
- **WHEN** a client sends `POST /api/plantillas` or `PATCH /api/plantillas/{id}` containing an undeclared property such as `"box": 1`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity`

### Requirement: Dynamic Free-Slot Derivation from Templates and Appointments
The system SHALL compute available appointment slots via `GET /api/disponibilidad?odontologo_id=&fecha=` by partitioning the dentist's templates for `fecha.weekday()` into slots of `duracion_slot_minutos` and excluding any slot intersecting an active appointment (`solicitado`, `confirmado`, `presente`, `ausente`) (`RN-AG-01`, `RN-AG-02`).

#### Scenario: Free slots calculated by subtracting active appointments (Expected Behavior)
- **WHEN** synthetic dentist Dra. Sofía Martín has a template on Monday (`09:00`–`10:30`, `duracion_slot_minutos=30`) and an existing appointment in state `solicitado` or `confirmado` from `09:30` to `10:00` on a future Monday
- **THEN** `GET /api/disponibilidad` responds with HTTP `200 OK` returning only the free slots `09:00–09:30` and `10:00–10:30` without exposing any patient data (`US-002 CA-1`, `CA-2`)

#### Scenario: Cancelled or annulled appointments release their time slot (Edge Case CB-03)
- **WHEN** synthetic dentist Dra. Sofía Martín has a template on Monday (`09:00`–`10:00`, `duracion_slot_minutos=30`) and the `09:00–09:30` appointment on that future Monday is in state `cancelado` or `anulado` (`RN-TU-04`)
- **THEN** `GET /api/disponibilidad` includes `09:00–09:30` and `09:30–10:00` as available free slots

#### Scenario: Template window not evenly divisible by slot duration discards incomplete remainder (Edge Case CB-02)
- **WHEN** a template covers `09:00` to `10:00` (`60` minutes) with `duracion_slot_minutos=40` on a future date with no appointments
- **THEN** `GET /api/disponibilidad` returns only the complete `09:00–09:40` slot and omits the incomplete 20-minute remainder (`09:40–10:00`)

#### Scenario: Appointment spanning or straddling several slots blocks every intersected slot (Edge Case CB-04)
- **WHEN** synthetic dentist Dra. Sofía Martín has a Monday template from `09:00` to `11:00` with `duracion_slot_minutos=30` and an active appointment (`confirmado`) from `09:15` to `10:15` on a future Monday
- **THEN** `GET /api/disponibilidad` excludes `09:00–09:30`, `09:30–10:00` and `10:00–10:30`, returning only `10:30–11:00`

#### Scenario: Availability query for a non-existent user or a non-dentist (Business Error CB-06)
- **WHEN** an authenticated user requests `GET /api/disponibilidad?odontologo_id=<id>&fecha=<future-date>` where `<id>` does not exist or belongs to a user whose `rol` is `paciente` or `recepcion`
- **THEN** the system responds with HTTP `404 Not Found` (user does not exist) or HTTP `422 Unprocessable Entity` (user is not a dentist)

### Requirement: Past Date and Elapsed Same-Day Slot Rejection
The system SHALL reject availability queries for dates prior to the current clinic date in `TIMEZONE` (`America/Argentina/Buenos_Aires`) and omit slots whose start time has already passed when querying the current date (`RN-GL-02`).

#### Scenario: Reject availability query for a past date (Business Error)
- **WHEN** an authenticated user requests `GET /api/disponibilidad?odontologo_id=<id>&fecha=<past-date>` where `fecha` is earlier than today in `America/Argentina/Buenos_Aires`
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` indicating that past dates cannot be queried (`RN-GL-02`)

#### Scenario: Same-day availability query filters out already elapsed morning slots (Edge Case CB-05)
- **WHEN** an authenticated user queries `GET /api/disponibilidad` for `fecha` equal to today when the clinic clock in `America/Argentina/Buenos_Aires` is `10:15` and the template runs `09:00`–`11:00` with 30-minute slots
- **THEN** the system omits `09:00–09:30`, `09:30–10:00`, and `10:00–10:30`, returning only `10:30–11:00`
