# Proposal: Dentist Features (C-15)

## Why

Los profesionales con rol `odontologo` cuentan actualmente con la ruta protegida `/odontologo/agenda` en el shell de aplicación, pero esta renderiza un contenedor placeholder sin conexión a la API. Con los endpoints de agenda propia del odontólogo (`C-09` — `GET /api/mis-turnos?fecha=YYYY-MM-DD`) y máquina de estados de turnos (`C-07` — `PATCH /api/turnos/{id}`) ya integrados en `main`, es necesario implementar la vista operativa del odontólogo para materializar las historias `US-007` (consultar exclusivamente sus propios turnos del día) y `US-008` (registrar asistencia real marcando `presente` o `ausente` sobre turnos confirmados).

## What Changes

- **Vista de Agenda Diaria del Odontólogo (`/odontologo/agenda` — `OdontologoAgendaPage`)**:
  - Consulta declarativa mediante TanStack Query (`useQuery`) a `GET /api/mis-turnos?fecha=YYYY-MM-DD` (sin enviar `fecha_desde` ni `fecha_hasta`, tal como exige el contrato de `C-09` para el rol `odontologo`), garantizando aislamiento estricto de propiedad en servidor (`odontologo_id == current_user.id`, `US-007 CA-1`, `RN-AU-02`).
  - Selector de fecha operativa (inicializado en la fecha local del consultorio en formato `YYYY-MM-DD`), filtro rápido por estado del turno en cliente y tarjetas de resumen diario (Total del día, Confirmados por atender, Presentes, Ausentes / Cancelados).
  - Visualización cronológica de los turnos propios del profesional (incluyendo turnos contiguos donde `fin_A == inicio_B` según `CB-01`) con rango horario (`HH:MM – HH:MM`), datos identificatorios del paciente (`nombre`, `nro_socio`, `email` sin exponer credenciales), motivo de consulta, badge de origen (`online` vs `recepcion`) y badge semántico de estado (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`).
  - Acciones de registro de asistencia real (`US-008 CA-1, CA-2`, `RN-TU-03`) mediante `useMutation` hacia **`PATCH /api/turnos/{id}`** con payload estricto `{ "estado": "presente" }` o `{ "estado": "ausente" }` (`extra="forbid"`, Reglas Duras #1, #8 y #9):
    - Botones **"Marcar presente"** y **"Marcar ausente"** habilitados exclusivamente cuando el turno se encuentra en estado `confirmado` (`confirmado → presente | ausente`).
    - Turnos en estado `solicitado`, `presente`, `ausente`, `cancelado` o `anulado` muestran su estado sin acciones de mutación habilitadas.
    - Manejo accesible (`role="alert"`) de errores de negocio devueltos por la API (`403 Forbidden` si se intentara operar sobre un turno ajeno según `RN-AU-02`/`RN-GL-01`, `409 Conflict` ante transiciones de estado inválidas según `RN-TU-03`, o `422 Unprocessable Entity` por parámetros de fecha inválidos).
- **Integración en Router (`frontend/src/router/routes.tsx`)**:
  - Reemplazo del nodo placeholder en `/odontologo/agenda` por el componente `OdontologoAgendaPage`.

## Capabilities

### New Capabilities
- `frontend-dentist-portal`: Vista interactiva, servicio HTTP tipado y hooks de TanStack Query para el portal del odontólogo (`/odontologo/agenda`), cubriendo la consulta de agenda diaria propia (`GET /api/mis-turnos?fecha=YYYY-MM-DD`) y el registro de asistencia real (`PATCH /api/turnos/{id}` con `estado: "presente" | "ausente"`).

### Modified Capabilities
<!-- Ninguna capacidad existente modifica sus requisitos de especificación; `dentist-agenda` y `appointment-state-machine` ya definen los contratos backend que esta capacidad consume. -->

## Impact

- **Frontend (`frontend/src/`)**:
  - Nuevos tipos de dominio y contratos API para odontólogo en `frontend/src/types/dentist.ts`.
  - Nuevo servicio HTTP tipado en `frontend/src/services/dentist.service.ts` sobre `apiClient` (`GET /api/mis-turnos?fecha=YYYY-MM-DD` y `PATCH /api/turnos/{id}`).
  - Nuevos hooks declarativos de TanStack Query en `frontend/src/hooks/useDentistAgenda.ts` (cero `useEffect` para data fetching — Regla Dura #6).
  - Nueva página en `PascalCase` (Regla Dura #5): `frontend/src/pages/OdontologoAgendaPage.tsx`.
  - Actualización de `frontend/src/router/routes.tsx` y su suite de tests.
- **Backend (`backend/`)**: Sin cambios en código backend; consume los contratos ya mergeados de `C-07` y `C-09`.
