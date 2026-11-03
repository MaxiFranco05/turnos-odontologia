# Proposal: Reception Features (C-14)

## Why

El personal de recepción (`rol="recepcion"`) cuenta actualmente con rutas protegidas en el shell de aplicación (`/recepcion/agenda` y `/recepcion/plantillas`), pero ambas renderizan contenedores placeholder sin conexión al backend. Con los endpoints de plantillas horarias (`C-05`), ciclo de vida de turnos (`C-07`) y agenda diaria clínica (`C-08`) ya integrados en `main`, es necesario construir las vistas operativas de recepción para materializar las historias `US-005` (agenda global diaria con confirmación/anulación de turnos) y `US-006` (configuración de plantillas semanales de disponibilidad por odontólogo).

## What Changes

- **Vista de Agenda Diaria de Recepción (`/recepcion/agenda` — `RecepcionAgendaPage`)**:
  - Consulta reactiva mediante TanStack Query (`useQuery`) a `GET /api/agenda/dia?fecha=YYYY-MM-DD[&odontologo_id=N]` (`RN-GL-01`).
  - Selector de fecha operativa (por defecto el día actual en formato `YYYY-MM-DD`) y filtro opcional por odontólogo (`odontologo_id`), más filtro visual rápido por estado del turno en cliente.
  - Visualización enriquecida de cada turno con horario (`inicio` – `fin`), datos del paciente (`nombre`, `nro_socio`, `email`), odontólogo asignado (`nombre`), motivo/prestación, badge de origen (`online` vs `recepcion`) y badge semántico de estado (`solicitado`, `confirmado`, `anulado`, `cancelado`, `presente`, `ausente`), preservando explícitamente la visibilidad de cancelaciones de pacientes (`estado="cancelado"`) y reservas web (`origen="online"`) para control operativo (`US-005 CA-1`, `CA-2`).
  - Acciones de transición de estado mediante `useMutation` hacia **`PATCH /api/turnos/{id}`** con body `{ "estado": "confirmado" }` o `{ "estado": "anulado" }` (`extra="forbid"`, alineado a las Reglas Duras #1, #8 y #9, corrigiendo la mención histórica a verbos `/confirmar` y `/anular` en `CHANGES.md`):
    - **Confirmar turno**: habilitado para turnos en estado `solicitado` (`solicitado → confirmado`, `RN-TU-02`).
    - **Anular turno**: habilitado para turnos en estado `solicitado` o `confirmado` (`solicitado | confirmado → anulado`), con confirmación previa y manejo explícito de errores de negocio (`422 Unprocessable Entity` cuando resta menos de 24 h de anticipación según `RN-TU-05`, y `409 Conflict` ante transiciones inválidas).
- **Vista de Gestión de Plantillas de Disponibilidad (`/recepcion/plantillas` — `RecepcionPlantillasPage`)**:
  - Listado semanal de bloques horarios por odontólogo consumiendo `GET /api/plantillas[?odontologo_id=N]` con agrupación legible por día de la semana (`0 = Lunes` a `6 = Domingo`).
  - Formulario validado de alta de plantilla (`POST /api/plantillas`) con `odontologo_id`, `dia_semana` (`0..6`), `hora_inicio`, `hora_fin`, `duracion_slot_minutos` y `prestacion` (`extra="forbid"`).
  - Edición parcial de plantillas existentes mediante `PATCH /api/plantillas/{id}` (Regla Dura #9) enviando únicamente los campos modificables (`dia_semana`, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`, `prestacion`) y baja lógica/física mediante `DELETE /api/plantillas/{id}` (`204 No Content`).
  - Manejo claro de errores de validación y solapamiento horario (`409 Conflict` cuando un bloque se superpone con otro del mismo odontólogo y día según `RN-AG-01` / `CB-04`, permitiendo adyacencia exacta `hora_fin == hora_inicio` según `CB-01`, y `422 Unprocessable Entity` si el `odontologo_id` no corresponde a un usuario con rol `odontologo` según `CB-06`).
- **Integración en Router (`frontend/src/router/routes.tsx`)**:
  - Reemplazo de los nodos placeholder en `/recepcion/agenda` y `/recepcion/plantillas` por los componentes `RecepcionAgendaPage` y `RecepcionPlantillasPage`.

## Capabilities

### New Capabilities
- `frontend-reception-portal`: Vistas interactivas, servicios tipados y hooks de TanStack Query para el portal de recepción (`/recepcion/agenda` y `/recepcion/plantillas`), abarcando consulta de agenda diaria clínica, confirmación y anulación de turnos (`PATCH /api/turnos/{id}`), y CRUD completo de plantillas semanales de disponibilidad (`GET/POST/PATCH/DELETE /api/plantillas`).

### Modified Capabilities
<!-- Ninguna capacidad existente cambia sus requisitos a nivel de especificación; `reception-agenda`, `appointment-state-machine` y `availability-engine` ya definen los contratos backend que esta capacidad consume. -->

## Impact

- **Frontend (`frontend/src/`)**:
  - Nuevos tipos de dominio y contratos API en `frontend/src/types/reception.ts`.
  - Nuevo servicio HTTP tipado en `frontend/src/services/reception.service.ts` sobre `apiClient` (`GET /api/agenda/dia`, `PATCH /api/turnos/{id}`, `GET/POST/PATCH/DELETE /api/plantillas`).
  - Nuevos hooks declarativos de TanStack Query en `frontend/src/hooks/useReceptionAgenda.ts` y `frontend/src/hooks/usePlantillas.ts` (cero `useEffect` para data fetching — Regla Dura #6).
  - Nuevas páginas en `PascalCase` (Regla Dura #5): `frontend/src/pages/RecepcionAgendaPage.tsx` y `frontend/src/pages/RecepcionPlantillasPage.tsx`.
  - Actualización de `frontend/src/router/routes.tsx` y su suite de tests.
- **Backend (`backend/`)**: Sin cambios en código backend; consume los contratos ya mergeados de `C-05`, `C-07` y `C-08`.
