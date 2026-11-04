# Technical Design — C-15: Dentist Features (`/odontologo/agenda`)

## 1. Context & Architecture Alignment

`C-15` implements the Dentist Portal view (`/odontologo/agenda`) on top of the existing React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query v5 architecture established in `C-11`, `C-12`, and `C-14`:

- **HTTP Client (`frontend/src/lib/api.ts`)**: Uses the central `apiClient` Axios instance which automatically injects `Authorization: Bearer <access_token>` and handles `401` token refresh / session expiration.
- **Role-Based Routing (`frontend/src/router/routes.tsx` & `ProtectedRoute.tsx`)**: `/odontologo/*` routes are guarded by `<ProtectedRoute allowedRoles={['odontologo']} />` (`RN-AU-02`, `CB-06`) and wrapped in `<AppLayout />`.
- **State & Server Cache**: Managed exclusively with TanStack Query (`useQuery`, `useMutation`, `useQueryClient`) — zero `useEffect` hooks for data fetching (Hard Rule #6).
- **Strict Validation Alignment**: All payloads sent to FastAPI match Pydantic v2 schemas configured with `ConfigDict(extra="forbid")` (Hard Rule #1).

---

## 2. Backend API Contracts Verified

### 2.1 Daily Self-Agenda (`GET /api/mis-turnos`)
Defined in `backend/app/api/mis_turnos.py`:
- **Query Parameters for `odontologo` role**:
  - `fecha: string` (`YYYY-MM-DD`, **required**).
  - `fecha_desde` and `fecha_hasta` **MUST NOT** be sent when authenticated as `odontologo` (backend explicitly raises `422 Unprocessable Entity` if present).
  - `odontologo_id` is **NOT** accepted; the backend extracts `current_user.id` directly from the JWT token (`RN-AU-02` BOLA protection).
- **Response (`200 OK`)**: `MisTurnosOdontologoItem[]` ordered by `inicio ASC, id ASC`:
  ```ts
  export interface TurnoPacienteResumen {
    id: number;
    nombre: string;
    nro_socio: string | null;
    email: string | null;
  }

  export interface MisTurnosOdontologoItem {
    id: number;
    paciente_id: number;
    odontologo_id: number;
    inicio: string; // ISO-8601 datetime
    fin: string;    // ISO-8601 datetime
    motivo: string;
    estado: TurnoEstado; // 'solicitado' | 'confirmado' | 'anulado' | 'cancelado' | 'presente' | 'ausente'
    origen: TurnoOrigen; // 'online' | 'recepcion'
    paciente: TurnoPacienteResumen;
  }
  ```

### 2.2 Attendance Recording (`PATCH /api/turnos/{id}`)
Defined in `backend/app/api/turnos.py` (`TurnoEstadoUpdate`):
- **Path Parameter**: `turnoId: number`
- **Request Body (`extra="forbid"`)**:
  ```ts
  export type TurnoAsistenciaEstado = 'presente' | 'ausente';

  export interface TurnoAsistenciaUpdateRequest {
    estado: TurnoAsistenciaEstado;
  }
  ```
- **Response (`200 OK`)**: `TurnoResponse` with updated `estado`.
- **Error Semantics**:
  - `403 Forbidden`: Dentist does not own the appointment (`turno.odontologo_id != current_user.id`) or attempts a transition reserved for another role.
  - `409 Conflict`: Appointment is not in `confirmado` status (`InvalidStateTransitionError`).
  - `422 Unprocessable Entity`: Invalid payload or undeclared field.

---

## 3. Frontend Module Design

```
frontend/src/
├── types/
│   └── dentist.ts                  # Strict TypeScript interfaces for MisTurnosOdontologoItem & TurnoAsistenciaUpdateRequest
├── services/
│   ├── dentist.service.ts          # getMisTurnosOdontologo(fecha) & updateTurnoAsistencia(turnoId, payload)
│   └── dentist.service.test.ts     # Unit tests verifying exact endpoints, query params, and extra="forbid" payload
├── hooks/
│   ├── useDentistAgenda.ts         # useDentistAgendaQuery(fecha) & useUpdateAsistenciaMutation()
│   └── useDentistAgenda.test.tsx   # Hook tests with QueryClientProvider
└── pages/
    ├── OdontologoAgendaPage.tsx    # Daily self-agenda view + Presente/Ausente actions
    └── OdontologoAgendaPage.test.tsx # Component & integration tests (states, CB-01 adjacency, 409/403 errors)
```

### 3.1 `frontend/src/types/dentist.ts`
Reuses `TurnoEstado`, `TurnoOrigen`, and `TurnoResponse` from `@/types/reception` so domain primitives remain single-sourced across the frontend. Defines `TurnoPacienteResumen`, `MisTurnosOdontologoItem`, `TurnoAsistenciaEstado`, and `TurnoAsistenciaUpdateRequest`.

### 3.2 `frontend/src/services/dentist.service.ts`
- `getMisTurnosOdontologo(fecha: string): Promise<MisTurnosOdontologoItem[]>`
  Calls `apiClient.get<MisTurnosOdontologoItem[]>('/mis-turnos', { params: { fecha } })`.
- `updateTurnoAsistencia(turnoId: number, payload: TurnoAsistenciaUpdateRequest): Promise<TurnoResponse>`
  Calls `apiClient.patch<TurnoResponse>(`/turnos/${turnoId}`, { estado: payload.estado })`.

### 3.3 `frontend/src/hooks/useDentistAgenda.ts`
- `useDentistAgendaQuery(fecha: string)`:
  - `queryKey: ['dentist-agenda', { fecha }]`
  - `queryFn: () => getMisTurnosOdontologo(fecha)`
  - `enabled: Boolean(fecha)`
- `useUpdateAsistenciaMutation()`:
  - Calls `updateTurnoAsistencia(turnoId, { estado })`
  - `onSuccess`: invalidates `['dentist-agenda']` and `['agenda-dia']` so both dentist and reception caches stay synchronized.

### 3.4 `frontend/src/pages/OdontologoAgendaPage.tsx`
- Reads `user` from `useAuthStore()` to greet the authenticated dentist (`user?.nombre`).
- Date filter `<Input type="date" />` initialized to today's local date (`YYYY-MM-DD`).
- Summary counters for the selected day: Total turnos, Confirmados pendientes de atención, Presentes, Ausentes.
- Chronological appointment table displaying:
  - Horario (`HH:mm - HH:mm` formatted cleanly; contiguous slots `09:00 - 09:30` and `09:30 - 10:00` render sequentially per `CB-01`).
  - Paciente (`paciente.nombre`, `paciente.nro_socio` badge or `"Sin N.º socio"`, and `paciente.email`).
  - Motivo (`motivo`) and Origen (`online` / `recepcion`).
  - Estado badge with semantic color coding (`confirmado`, `presente`, `ausente`, `solicitado`, `cancelado`, `anulado`).
  - Acciones de Asistencia:
    - If `turno.estado === 'confirmado'`: renders `"Presente"` and `"Ausente"` buttons (disabled while a mutation is pending).
    - For any other state (`presente`, `ausente`, `solicitado`, `cancelado`, `anulado`): renders a read-only label (`"Asistencia registrada"` or `"Sin acciones disponibles"`), preventing invalid state transitions (`RN-TU-03`).
- Error handling: extracts backend `detail` message from Axios errors (`403`, `409`, `422`, `500`) and displays it inside `<Alert variant="destructive" role="alert">` without unmounting the table.

---

## 4. UI Mockups
Decision: no (project policy — `visual_design.mode: "off"` in `.active-orchestrator-state.json` and `Mode: off` in `design-system/README.md`).
