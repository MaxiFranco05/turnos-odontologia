# Technical Design — C-13: Patient Features (`/paciente/disponibilidad` & `/paciente/mis-turnos`)

## 1. Context & Architecture Alignment

`C-13` completes Phase 5 (Frontend) by implementing the two views of the Patient Portal (`/paciente/disponibilidad` and `/paciente/mis-turnos`) on top of the React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query v5 stack:

- **HTTP Client (`frontend/src/lib/api.ts`)**: Uses `apiClient` with automatic Bearer JWT header injection and `401` refresh/logout handling.
- **Role-Based Routing (`frontend/src/router/routes.tsx` & `ProtectedRoute.tsx`)**: `/paciente/*` routes are guarded by `<ProtectedRoute />` and navigated via `<AppLayout />` (`"Buscar turno"` → `/paciente/disponibilidad`, `"Mis turnos"` → `/paciente/mis-turnos`).
- **Declarative Server State**: Managed 100% via TanStack Query (`useQuery`, `useMutation`, `useQueryClient`) with zero `useEffect` for data fetching (Hard Rule #6).
- **Strict Pydantic Contract Alignment**: Request bodies and query params match backend schemas configured with `ConfigDict(extra="forbid")` (Hard Rule #1).

---

## 2. Backend API Contracts Verified

### 2.1 Free-Slot Availability (`GET /api/disponibilidad`)
Defined in `backend/app/api/disponibilidad.py` & `backend/app/application/availability.py`:
- **Query Parameters**:
  - `odontologo_id: number` (required, `> 0`)
  - `fecha: string` (`YYYY-MM-DD`, required, `>= today` in clinic timezone `RN-GL-02`)
- **Response (`200 OK`)**: `SlotDisponibleItem[]`:
  ```ts
  export interface SlotDisponibleItem {
    inicio: string; // ISO-8601 datetime with clinic offset
    fin: string;    // ISO-8601 datetime with clinic offset
    odontologo_id: number;
    prestacion: string;
  }
  ```
- **Error Semantics**:
  - `404 Not Found`: Dentist ID does not exist.
  - `422 Unprocessable Entity`: Date is in the past (`RN-GL-02`) or user is not an `odontologo` (`CB-06`).

### 2.2 Online Appointment Request (`POST /api/turnos`)
Defined in `backend/app/api/turnos.py` (`TurnoCreate`):
- **Request Body (`extra="forbid"`, `str_strip_whitespace=True`)**:
  ```ts
  export interface TurnoCreatePayload {
    odontologo_id: number;
    inicio: string;
    fin: string;
    motivo: string;
  }
  ```
  *(Note: `paciente_id`, `estado`, and `origen` MUST NOT be sent; backend binds `paciente_id = current_user.id`, `estado = 'solicitado'`, `origen = 'online'`.)*
- **Response (`201 Created`)**: `TurnoResponseItem`.
- **Error Semantics**:
  - `409 Conflict`: Slot already occupied (`RN-AG-01`).
  - `422 Unprocessable Entity`: Slot not aligned with template (`RN-AG-02`, `CB-02`), past/elapsed timestamp (`RN-GL-02`, `CB-05`), or empty `motivo`.

### 2.3 Patient Self-Appointments (`GET /api/mis-turnos`)
Defined in `backend/app/api/mis_turnos.py` (`MisTurnosPacienteItemResponse`):
- **Query Parameters for `paciente` role**:
  - `fecha_desde?: string` (`YYYY-MM-DD`, optional)
  - `fecha_hasta?: string` (`YYYY-MM-DD`, optional, `>= fecha_desde`)
  - `fecha` **MUST NOT** be sent when authenticated as `paciente` (backend raises `422`).
- **Response (`200 OK`)**: `MisTurnosPacienteItem[]`:
  ```ts
  export interface TurnoOdontologoResumen {
    id: number;
    nombre: string;
    nro_socio: string | null;
    email: string | null;
  }

  export interface MisTurnosPacienteItem {
    id: number;
    paciente_id: number;
    odontologo_id: number;
    inicio: string;
    fin: string;
    motivo: string;
    estado: EstadoTurno;
    origen: OrigenTurno;
    odontologo: TurnoOdontologoResumen;
  }
  ```

### 2.4 Patient Appointment Cancellation (`PATCH /api/turnos/{id}`)
Defined in `backend/app/api/turnos.py` (`TurnoEstadoUpdate`):
- **Request Body (`extra="forbid"`)**:
  ```ts
  export interface TurnoCancelPayload {
    estado: 'cancelado';
  }
  ```
- **Error Semantics**:
  - `422 Unprocessable Entity`: Less than 24 hours anticipation (`AnticipationWindowError`, `RN-TU-05`).
  - `409 Conflict`: Appointment is not in `solicitado` or `confirmado` state (`InvalidStateTransitionError`).
  - `403 Forbidden`: Appointment belongs to another patient (`UnauthorizedTransitionError`).

---

## 3. Frontend Module Design

```
frontend/src/
├── types/
│   └── patient.ts                        # SlotDisponibleItem, TurnoCreatePayload, MisTurnosPacienteItem, TurnoCancelPayload
├── services/
│   ├── patient.service.ts                # getDisponibilidad, createTurnoOnline, getMisTurnosPaciente, cancelarTurnoPaciente
│   └── patient.service.test.ts           # Unit tests verifying exact endpoints, query params, and extra="forbid" bodies
├── hooks/
│   ├── usePatientPortal.ts               # useDisponibilidadQuery, useCreateTurnoMutation, useMisTurnosPacienteQuery, useCancelarTurnoMutation
│   └── usePatientPortal.test.tsx         # Hook tests with QueryClientProvider and cache invalidation assertions
└── pages/
    ├── PacienteDisponibilidadPage.tsx    # Free-slot search + online booking confirmation form
    ├── PacienteDisponibilidadPage.test.tsx
    ├── PacienteMisTurnosPage.tsx         # Self-appointments list + date range filter + 24h cancellation
    └── PacienteMisTurnosPage.test.tsx
```

---

## 4. UI Mockups
Decision: no (project policy — `visual_design.mode: "off"` in `.active-orchestrator-state.json` and `Mode: off` in `design-system/README.md`).
