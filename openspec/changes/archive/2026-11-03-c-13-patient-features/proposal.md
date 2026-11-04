# Proposal: Patient Features (C-13)

## Why

Los pacientes autenticados (`rol: 'paciente'`) cuentan actualmente con las rutas protegidas `/paciente/disponibilidad` y `/paciente/mis-turnos` en el shell de aplicación, pero ambas renderizan contenedores placeholder. Con los endpoints backend del motor de disponibilidad (`C-05` — `GET /api/disponibilidad`), solicitud online de turnos (`C-06` — `POST /api/turnos`), máquina de estados y cancelación con anticipación mínima (`C-07` — `PATCH /api/turnos/{id}`) y listado de turnos propios (`C-10` — `GET /api/mis-turnos?fecha_desde=&fecha_hasta=`) ya integrados en `main`, es necesario implementar las vistas interactivas del portal del paciente para completar las historias de usuario `US-002` (consultar disponibilidad horaria), `US-003` (solicitar turno online) y `US-004` (consultar y cancelar turnos propios).

## What Changes

- **Vista de Disponibilidad y Solicitud Online de Turnos (`/paciente/disponibilidad` — `PacienteDisponibilidadPage`)**:
  - Consulta declarativa mediante TanStack Query (`useQuery`) a `GET /api/disponibilidad?odontologo_id=<id>&fecha=YYYY-MM-DD` (`US-002`, `RN-AG-01`, `RN-AG-02`, `RN-GL-02`).
  - Selector de ID de odontólogo y fecha operativa (con fecha mínima en el día actual del consultorio según `RN-GL-02`), mostrando la grilla de huecos libres (`SlotDisponible`: `inicio`, `fin`, `odontologo_id`, `prestacion`) sin exponer datos de otros pacientes (`US-002 CA-2`, Regla Dura #12).
  - Formulario / panel interactivo de confirmación de solicitud al seleccionar un hueco libre (`US-003`, `Flujo 2`), con campo obligatorio `motivo` y envío mediante `useMutation` hacia **`POST /api/turnos`** con payload estricto `{ odontologo_id, inicio, fin, motivo }` (`extra="forbid"`, sin enviar `paciente_id`, `estado` ni `origen` según Regla Dura #1 y protección OWASP BOLA/BOPLA).
  - Manejo accesible (`role="alert"`) de errores de negocio: `409 Conflict` cuando un hueco es tomado concurrentemente (`RN-AG-01`, `CB-04`), `422 Unprocessable Entity` para fechas pasadas, horarios ya transcurridos hoy (`CB-05`), slots desalineados (`CB-02`) o usuario que no posee rol `odontologo` (`CB-06`), y `404 Not Found` para odontólogo inexistente.
- **Vista de Mis Turnos y Cancelación (`/paciente/mis-turnos` — `PacienteMisTurnosPage`)**:
  - Consulta declarativa mediante TanStack Query (`useQuery`) a `GET /api/mis-turnos` con filtros opcionales `fecha_desde` y `fecha_hasta` (sin enviar nunca el parámetro exclusivo de odontólogo `fecha`, `US-004`, `Flujo 5`), garantizando aislamiento de propiedad en servidor (`paciente_id == current_user.id`, `RN-AU-02`).
  - Listado cronológico de turnos propios con fecha y rango horario (`HH:MM – HH:MM`), datos del profesional (`odontologo.nombre`, `odontologo.email`), motivo, origen (`online` / `recepcion`) y badge semántico de estado (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`).
  - Acción **"Cancelar turno"** (`US-004 CA-1, CA-2`, `RN-TU-02`, `RN-TU-04`, `RN-TU-05`) habilitada únicamente sobre turnos activos elegibles (`solicitado` o `confirmado`), enviando **`PATCH /api/turnos/{id}`** con payload estricto `{ "estado": "cancelado" }` (`extra="forbid"`, Reglas Duras #1, #8 y #9).
  - Manejo accesible (`role="alert"`) del rechazo `422 Unprocessable Entity` cuando se intenta cancelar con menos de 24 horas de anticipación (`AnticipationWindowError`, `RN-TU-05`) o `409 Conflict` ante transiciones inválidas.
- **Integración en Router (`frontend/src/router/routes.tsx`)**:
  - Reemplazo de los nodos placeholder en `/paciente/disponibilidad` y `/paciente/mis-turnos` por `PacienteDisponibilidadPage` y `PacienteMisTurnosPage`.

## Capabilities

### New Capabilities
- `frontend-patient-portal`: Vistas interactivas, servicio HTTP tipado y hooks de TanStack Query para el portal del paciente (`/paciente/disponibilidad` y `/paciente/mis-turnos`), cubriendo consulta de huecos libres (`GET /api/disponibilidad`), solicitud online de turnos (`POST /api/turnos`), consulta de turnos propios (`GET /api/mis-turnos`) y cancelación con anticipación mínima (`PATCH /api/turnos/{id}`).

### Modified Capabilities
<!-- Ninguna capacidad existente modifica sus requisitos; `availability-engine`, `appointment-request`, `appointment-state-machine` y `patient-portal` ya definen los contratos backend consumidos. -->

## Impact

- **Frontend (`frontend/src/`)**:
  - Nuevos tipos de dominio y contratos API para paciente en `frontend/src/types/patient.ts`.
  - Nuevo servicio HTTP tipado en `frontend/src/services/patient.service.ts` sobre `apiClient` (`GET /api/disponibilidad`, `POST /api/turnos`, `GET /api/mis-turnos`, `PATCH /api/turnos/{id}`).
  - Nuevos hooks declarativos de TanStack Query en `frontend/src/hooks/usePatientPortal.ts` (cero `useEffect` para data fetching — Regla Dura #6).
  - Nuevas páginas en `PascalCase` (Regla Dura #5): `frontend/src/pages/PacienteDisponibilidadPage.tsx` y `frontend/src/pages/PacienteMisTurnosPage.tsx`.
  - Actualización de `frontend/src/router/routes.tsx` y `frontend/src/router/router.test.tsx`.
- **Backend (`backend/`)**: Sin cambios en código backend; consume los contratos ya mergeados de `C-05`, `C-06`, `C-07` y `C-10`.
- **Governance Level**: **MEDIUM** (lógica de negocio cliente e integración de flujos E2E 2 y 5 con validación de reglas de dominio).
