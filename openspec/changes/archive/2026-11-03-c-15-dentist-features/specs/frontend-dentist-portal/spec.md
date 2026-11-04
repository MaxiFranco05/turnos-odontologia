# frontend-dentist-portal Specification

## Purpose
Provide the React + TypeScript Frontend Dentist Portal (`/odontologo/agenda`) so authenticated dentists can consult their own daily schedule (`GET /api/mis-turnos?fecha=YYYY-MM-DD`) and record patient attendance (`PATCH /api/turnos/{id}` with `presente` or `ausente`) in strict compliance with BOLA ownership rules (`RN-AU-02`) and appointment state machine transitions (`RN-TU-03`, `RN-GL-01`).

## ADDED Requirements

### Requirement: Dentist Daily Self-Agenda View
The system MUST provide a daily agenda view at `/odontologo/agenda` that queries `GET /api/mis-turnos?fecha=YYYY-MM-DD` via TanStack Query without sending `odontologo_id`, `fecha_desde`, or `fecha_hasta`, displaying appointments chronologically with patient details (`nombre`, `nro_socio`, `email`), time range (`inicio`–`fin`), `motivo`, `origen`, and visual status badges.

#### Scenario: Consultar agenda diaria propia ordenada cronológicamente (Expected Behavior)
- **GIVEN** an authenticated user with role `odontologo` (e.g., synthetic dentist "Dr. Martín Ruiz") on `/odontologo/agenda`
- **WHEN** the page loads for the selected date `2026-11-10`
- **THEN** the client executes `GET /api/mis-turnos?fecha=2026-11-10` without `odontologo_id`, `fecha_desde`, or `fecha_hasta` parameters
- **AND** renders each returned appointment ordered by `inicio` ascending with start/end times (`HH:mm`), patient name (e.g., "Lucía Gómez"), membership number (`SOC-1001`), reason (`Control general`), origin badge (`online` or `recepcion`), and current status badge (`confirmado`, `solicitado`, `presente`, `ausente`, `cancelado`, or `anulado`).

#### Scenario: Cambio de fecha o agenda vacía sin turnos (Expected Behavior / Empty State)
- **GIVEN** an authenticated dentist viewing `/odontologo/agenda`
- **WHEN** the dentist selects a date (e.g., `2026-11-12`) for which `GET /api/mis-turnos?fecha=2026-11-12` returns an empty list `[]`
- **THEN** the view displays a clear empty-state message indicating there are no scheduled appointments for that date and does not render any error alert.

#### Scenario: Turnos contiguos adyacentes sin falso solapamiento visual (Edge Case - CB-01)
- **GIVEN** `GET /api/mis-turnos?fecha=2026-11-10` returns two contiguous appointments where Appointment A runs from `09:00` to `09:30` and Appointment B runs from `09:30` to `10:00` (`fin_A == inicio_B`)
- **WHEN** the daily agenda table renders both appointments
- **THEN** both rows are displayed sequentially (`09:00 - 09:30` followed by `09:30 - 10:00`) without any visual overlap warning or layout collision.

#### Scenario: Error de validación o de servidor al consultar la agenda (Business/HTTP Error)
- **GIVEN** an authenticated dentist on `/odontologo/agenda`
- **WHEN** `GET /api/mis-turnos` fails with HTTP `422` or `500`
- **THEN** the view renders an accessible destructive alert (`role="alert"`) describing the failure so the dentist can retry or adjust the selected date.

---

### Requirement: Patient Attendance Recording (`Presente` / `Ausente`)
The system MUST allow an authenticated dentist to record attendance on their own appointments in `confirmado` status by sending `PATCH /api/turnos/{id}` with payload `{ "estado": "presente" }` or `{ "estado": "ausente" }` (`extra="forbid"`), disabling or hiding attendance actions for any other appointment state and invalidating agenda queries upon completion.

#### Scenario: Marcar turno confirmado como Presente o Ausente exitosamente (Expected Behavior)
- **GIVEN** an authenticated dentist viewing `/odontologo/agenda` with an appointment `#501` in status `confirmado` for synthetic patient "Lucía Gómez"
- **WHEN** the dentist clicks the "Presente" (or "Ausente") action button on appointment `#501`
- **THEN** the client sends `PATCH /api/turnos/501` with exact JSON body `{ "estado": "presente" }` (or `{ "estado": "ausente" }`) and no extra properties
- **AND** upon receiving `200 OK`, invalidates the TanStack Query cache (`['dentist-agenda']` and `['agenda-dia']`), displays a confirmation status banner (`role="status"`), and updates the row badge to `presente` (or `ausente`) without action buttons.

#### Scenario: Ocultar acciones de asistencia en estados no elegibles (Edge Case - RN-TU-03 / CB-03)
- **GIVEN** an authenticated dentist viewing `/odontologo/agenda` containing appointments in states `solicitado`, `presente`, `ausente`, `cancelado`, or `anulado`
- **WHEN** the appointment rows are rendered
- **THEN** the "Presente" and "Ausente" buttons are NOT rendered or are disabled for those rows, ensuring only appointments in `confirmado` status expose attendance transition triggers.

#### Scenario: Rechazo por conflicto de estado o permiso BOLA al registrar asistencia (Business Error 409 / 403)
- **GIVEN** an authenticated dentist attempting to mark attendance on appointment `#501`
- **WHEN** `PATCH /api/turnos/501` responds with HTTP `409 Conflict` (`InvalidStateTransitionError` because the appointment was cancelled concurrently) or HTTP `403 Forbidden` (`UnauthorizedTransitionError`)
- **THEN** the view catches the error and displays an accessible error alert (`role="alert"`) with the backend detail message without crashing the agenda view.
