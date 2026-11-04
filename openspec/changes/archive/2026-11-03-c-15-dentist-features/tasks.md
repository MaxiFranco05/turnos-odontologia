# Tasks — C-15: Dentist Features (`/odontologo/agenda`)

## 1. Domain Contracts & Dentist API Service (Strict TDD)

- [x] 1.1 Create `frontend/src/types/dentist.ts` defining strict TypeScript interfaces (`TurnoPacienteResumen`, `MisTurnosOdontologoItem`, `TurnoAsistenciaEstado`, `TurnoAsistenciaUpdateRequest`) without `any` (Hard Rule #4), and verify `npx tsc --noEmit` passes.
- [x] 1.2 Write failing unit tests in `frontend/src/services/dentist.service.test.ts` (RED) covering `getMisTurnosOdontologo(fecha)` (`GET /api/mis-turnos?fecha=YYYY-MM-DD` without `odontologo_id`, `fecha_desde`, or `fecha_hasta`) and `updateTurnoAsistencia(turnoId, payload)` (`PATCH /api/turnos/{id}` with exact `{ estado: 'presente' | 'ausente' }` payload per Hard Rule #1), then implement `frontend/src/services/dentist.service.ts` (GREEN) and verify `npx vitest run src/services/dentist.service.test.ts` passes.

## 2. TanStack Query Hooks for Dentist Self-Agenda & Attendance (Strict TDD)

- [x] 2.1 Write failing hook tests in `frontend/src/hooks/useDentistAgenda.test.tsx` (RED) verifying `useDentistAgendaQuery(fecha)` fetches via `getMisTurnosOdontologo` without `useEffect` (Hard Rule #6) and `useUpdateAsistenciaMutation()` calls `updateTurnoAsistencia` and invalidates `['dentist-agenda']` and `['agenda-dia']` query keys, then implement `frontend/src/hooks/useDentistAgenda.ts` (GREEN) and verify `npx vitest run src/hooks/useDentistAgenda.test.tsx` passes.

## 3. Dentist Daily Agenda Page (`/odontologo/agenda`) & Router Wiring (Strict TDD)

- [x] 3.1 Write failing component and integration tests in `frontend/src/pages/OdontologoAgendaPage.test.tsx` (RED) using synthetic data (`Dr. Martín Ruiz`, `Lucía Gómez` — Hard Rule #12) covering: (a) chronological daily agenda rendering with patient details and status badges, (b) empty state when a selected date has no appointments, (c) contiguous appointments (`09:00-09:30` and `09:30-10:00`, `CB-01`) rendered sequentially without overlap warnings, (d) marking a `confirmado` appointment as `presente` or `ausente` via `PATCH /api/turnos/{id}`, (e) hiding/disabling attendance buttons on non-`confirmado` states (`solicitado`, `presente`, `ausente`, `cancelado`, `anulado`), and (f) accessible `role="alert"` error banner on HTTP `409` / `403` / `500` errors.
- [x] 3.2 Implement `frontend/src/pages/OdontologoAgendaPage.tsx` (PascalCase per Hard Rule #5) and replace the `/odontologo/agenda` placeholder in `frontend/src/router/routes.tsx` (GREEN + REFACTOR), verifying `npx vitest run src/pages/OdontologoAgendaPage.test.tsx` passes.

## 4. Full Suite Regression & Production Build Verification

- [x] 4.1 Run the full frontend test suite (`npx vitest run`) and production build (`npm run build` inside `frontend/`) and verify 100% of test suites pass with zero TypeScript or Vite bundling errors.

## Workflow follow-up

- Run `/opsx:archive c-15-dentist-features` after implementation and verification are complete to sync `frontend-dentist-portal` delta specs into `openspec/specs/` and mark `C-15` as `[x]` in `CHANGES.md`.
