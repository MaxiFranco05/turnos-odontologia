# Tasks — C-13: Patient Features (`/paciente/disponibilidad` & `/paciente/mis-turnos`)

## 1. Domain Contracts & Patient API Service (Strict TDD)

- [x] 1.1 Create `frontend/src/types/patient.ts` defining strict TypeScript interfaces (`SlotDisponibleItem`, `DisponibilidadQueryParams`, `TurnoCreatePayload`, `TurnoOdontologoResumen`, `MisTurnosPacienteItem`, `MisTurnosPacienteQueryParams`, `TurnoCancelPayload`) without `any` (Hard Rule #4), and verify `npx tsc --noEmit` passes.
- [x] 1.2 Write failing unit tests in `frontend/src/services/patient.service.test.ts` (RED) covering `getDisponibilidad`, `createTurnoOnline` (`POST /api/turnos` with exact `{ odontologo_id, inicio, fin, motivo }` per Hard Rule #1), `getMisTurnosPaciente` (`GET /api/mis-turnos` with optional `fecha_desde`/`fecha_hasta` and never `fecha`), and `cancelarTurnoPaciente` (`PATCH /api/turnos/{id}` with `{ estado: 'cancelado' }`), then implement `frontend/src/services/patient.service.ts` (GREEN) and verify `npx vitest run src/services/patient.service.test.ts` passes.

## 2. TanStack Query Hooks for Patient Portal (Strict TDD)

- [x] 2.1 Write failing hook tests in `frontend/src/hooks/usePatientPortal.test.tsx` (RED) verifying `useDisponibilidadQuery`, `useCreateTurnoMutation`, `useMisTurnosPacienteQuery`, and `useCancelarTurnoMutation` operate without `useEffect` (Hard Rule #6) and invalidate `['patient-disponibilidad']`, `['patient-mis-turnos']`, and `['agenda-dia']` upon mutations, then implement `frontend/src/hooks/usePatientPortal.ts` (GREEN) and verify `npx vitest run src/hooks/usePatientPortal.test.tsx` passes.

## 3. Patient Availability & Online Booking Page (`/paciente/disponibilidad`) (Strict TDD)

- [x] 3.1 Write failing component and integration tests in `frontend/src/pages/PacienteDisponibilidadPage.test.tsx` (RED) using synthetic data (`Dr. Martín Ruiz`, `Lucía Gómez` — Hard Rule #12) covering: (a) querying and rendering free slots including contiguous slots (`CB-01`), (b) empty state when no slots are available, (c) selecting a slot, validating non-empty `motivo`, and submitting `POST /api/turnos` (`US-003`), and (d) accessible `role="alert"` error banners on HTTP `409` overlap conflict (`RN-AG-01` / `CB-04`) and HTTP `422` past date / invalid dentist role (`RN-GL-02` / `CB-06`).
- [x] 3.2 Implement `frontend/src/pages/PacienteDisponibilidadPage.tsx` (PascalCase per Hard Rule #5) (GREEN + REFACTOR) and verify `npx vitest run src/pages/PacienteDisponibilidadPage.test.tsx` passes.

## 4. Patient Self-Appointments & Cancellation Page (`/paciente/mis-turnos`) & Router Wiring (Strict TDD)

- [x] 4.1 Write failing component and integration tests in `frontend/src/pages/PacienteMisTurnosPage.test.tsx` (RED) using synthetic data (`Lucía Gómez`, `Dr. Martín Ruiz` — Hard Rule #12) covering: (a) listing own appointments chronologically with dentist details and status badges (`US-004`), (b) filtering by `fecha_desde` and `fecha_hasta`, (c) cancelling an active appointment (`solicitado` or `confirmado`) via `PATCH /api/turnos/{id}` with `{ estado: 'cancelado' }` (`RN-TU-04` / `CB-03`), (d) hiding cancel buttons on terminal states (`cancelado`, `anulado`, `presente`, `ausente`), and (e) accessible `role="alert"` error banner when cancellation fails with HTTP `422` due to `< 24h` anticipation (`RN-TU-05`).
- [x] 4.2 Implement `frontend/src/pages/PacienteMisTurnosPage.tsx` (PascalCase per Hard Rule #5) and mount both `PacienteDisponibilidadPage` and `PacienteMisTurnosPage` in `frontend/src/router/routes.tsx` (GREEN + REFACTOR), verifying `npx vitest run src/pages/PacienteMisTurnosPage.test.tsx src/router/router.test.tsx` passes.

## 5. Full Suite Regression & Production Build Verification

- [x] 5.1 Run the full frontend test suite (`npx vitest run`) and production build (`npm run build` inside `frontend/`) and verify 100% of test suites pass with zero TypeScript or Vite bundling errors.

## Workflow follow-up

- Run `/opsx:archive c-13-patient-features` after implementation and verification are complete to sync `frontend-patient-portal` delta specs into `openspec/specs/` and mark `C-13` as `[x]` in `CHANGES.md`.
