# frontend-patient-portal Specification

## Purpose
Provide the React + TypeScript Frontend Patient Portal (`/paciente/disponibilidad` and `/paciente/mis-turnos`) so authenticated patients can query available dental slots (`GET /api/disponibilidad`), request online appointments (`POST /api/turnos`), list their own appointments (`GET /api/mis-turnos`), and cancel active appointments (`PATCH /api/turnos/{id}`) in strict compliance with `RN-AG-01`, `RN-AG-02`, `RN-TU-01`..`05`, `RN-GL-01`, `RN-GL-02`, and `RN-AU-02`.

## Requirements

### Requirement: Patient Free-Slot Availability Search
The system MUST provide an availability search view at `/paciente/disponibilidad` that queries `GET /api/disponibilidad?odontologo_id=<id>&fecha=YYYY-MM-DD` via TanStack Query and displays bookable slots (`inicio`, `fin`, `prestacion`) without exposing any other patient's personal data.

#### Scenario: Consultar huecos disponibles de un odontólogo en una fecha futura (Expected Behavior)
- **GIVEN** an authenticated user with role `paciente` (e.g., synthetic patient "Lucía Gómez") on `/paciente/disponibilidad`
- **WHEN** the patient selects dentist ID `2` (e.g., synthetic dentist "Dr. Martín Ruiz") and date `2026-11-23`
- **THEN** the client executes `GET /api/disponibilidad?odontologo_id=2&fecha=2026-11-23`
- **AND** renders the returned free slots (`SlotDisponible`) showing time range (`HH:mm – HH:mm`) and service (`prestacion`, e.g., `"Consulta general"`) with a button to select each slot, including contiguous slots (`09:00 – 09:30` and `09:30 – 10:00` per `CB-01`) and slots released by cancelled/annulled appointments (`CB-03`).

#### Scenario: Fecha sin huecos disponibles muestra estado vacío claro (Expected Behavior / Empty State)
- **GIVEN** an authenticated patient on `/paciente/disponibilidad`
- **WHEN** `GET /api/disponibilidad` returns an empty list `[]` for the selected dentist and date
- **THEN** the view renders an informative empty-state message indicating no available slots exist for that selection without rendering an error alert.

#### Scenario: Rechazo por fecha pasada o ID de usuario que no es odontólogo (Business Error 422 / 404 - RN-GL-02, CB-06)
- **GIVEN** an authenticated patient querying availability on `/paciente/disponibilidad`
- **WHEN** `GET /api/disponibilidad` fails with HTTP `422 Unprocessable Entity` (past date per `RN-GL-02` or target user is not an `odontologo` per `CB-06`) or HTTP `404 Not Found`
- **THEN** the view displays an accessible error alert (`role="alert"`) with the backend detail message.

---

### Requirement: Online Appointment Request Submission
The system MUST allow an authenticated patient on `/paciente/disponibilidad` to select an available slot, enter a non-empty `motivo`, and submit `POST /api/turnos` with exact payload `{ odontologo_id, inicio, fin, motivo }` (`extra="forbid"`), creating the appointment in `solicitado` status and invalidating availability and self-appointment caches.

#### Scenario: Solicitar turno online exitosamente sobre un hueco disponible (Expected Behavior - US-003, Flujo 2)
- **GIVEN** an authenticated patient viewing available slot `09:00 – 09:30` (`2026-11-23T09:00:00-03:00` to `2026-11-23T09:30:00-03:00`) for dentist ID `2`
- **WHEN** the patient selects the slot, enters `motivo` `"Control anual y limpieza"`, and submits the booking form
- **THEN** the client sends `POST /api/turnos` with exact JSON body `{ "odontologo_id": 2, "inicio": "2026-11-23T09:00:00-03:00", "fin": "2026-11-23T09:30:00-03:00", "motivo": "Control anual y limpieza" }` and no undeclared fields (`paciente_id`, `estado`, `origen` omitted)
- **AND** upon receiving `201 Created`, invalidates `['patient-disponibilidad']` and `['patient-mis-turnos']` caches and displays a confirmation status banner (`role="status"`).

#### Scenario: Validación cliente de motivo obligatorio antes de enviar (Edge Case)
- **GIVEN** an authenticated patient who selected an available slot on `/paciente/disponibilidad`
- **WHEN** the patient attempts to submit the request with an empty or whitespace-only `motivo`
- **THEN** the form prevents the HTTP call and displays a validation error message requiring the consultation reason.

#### Scenario: Conflicto 409 por solapamiento concurrente al reservar hueco (Business Error 409 - RN-AG-01, CB-04)
- **GIVEN** an authenticated patient submitting an appointment request for slot `09:00 – 09:30`
- **WHEN** `POST /api/turnos` responds with HTTP `409 Conflict` because the slot was just taken (`RN-AG-01`)
- **THEN** the view displays an accessible destructive alert (`role="alert"`) informing the patient of the schedule conflict so they can pick another slot.

---

### Requirement: Patient Self-Appointment Listing and Cancellation
The system MUST provide a self-appointment view at `/paciente/mis-turnos` that queries `GET /api/mis-turnos` (with optional `fecha_desde` and `fecha_hasta`, never sending `fecha`) and allows cancelling appointments in `solicitado` or `confirmado` status via `PATCH /api/turnos/{id}` with payload `{ "estado": "cancelado" }` (`extra="forbid"`).

#### Scenario: Listar mis turnos ordenados cronológicamente con filtros de rango opcionales (Expected Behavior - US-004, Flujo 5)
- **GIVEN** an authenticated patient "Lucía Gómez" on `/paciente/mis-turnos`
- **WHEN** the page loads (or when the patient filters by `fecha_desde` and `fecha_hasta`)
- **THEN** the client executes `GET /api/mis-turnos` without the dentist-only `fecha` parameter
- **AND** renders each appointment with date/time, dentist name (`odontologo.nombre`), `motivo`, `origen` badge, and current `estado` badge (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`).

#### Scenario: Cancelar un turno propio activo con al menos 24h de anticipación (Expected Behavior - RN-TU-04, CB-03)
- **GIVEN** an authenticated patient viewing `/paciente/mis-turnos` with appointment `#601` in status `confirmado` (or `solicitado`)
- **WHEN** the patient clicks the "Cancelar turno" button on appointment `#601`
- **THEN** the client sends `PATCH /api/turnos/601` with exact JSON body `{ "estado": "cancelado" }`
- **AND** upon receiving `200 OK`, invalidates `['patient-mis-turnos']`, `['patient-disponibilidad']`, and `['agenda-dia']`, displays a status confirmation (`role="status"`), and hides the cancel button for that cancelled appointment.

#### Scenario: Ocultar botón de cancelación en estados terminales o pasados (Edge Case - RN-TU-03)
- **GIVEN** an authenticated patient viewing `/paciente/mis-turnos` with appointments in states `cancelado`, `anulado`, `presente`, or `ausente`
- **WHEN** the rows are rendered
- **THEN** no "Cancelar turno" action button is rendered for those rows.

#### Scenario: Rechazo 422 al intentar cancelar con menos de 24 horas de anticipación (Business Error 422 - RN-TU-05)
- **GIVEN** an authenticated patient attempting to cancel appointment `#602` on `/paciente/mis-turnos`
- **WHEN** `PATCH /api/turnos/602` responds with HTTP `422 Unprocessable Entity` (`AnticipationWindowError` because less than 24 hours remain before `inicio`)
- **THEN** the view catches the error and renders an accessible destructive alert (`role="alert"`) displaying the backend anticipation rule message.
