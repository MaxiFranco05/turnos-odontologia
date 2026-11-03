# Tasks: Reception Features (C-14)

## 1. Tipos de Dominio y Servicio HTTP (`reception.service.ts`)

- [x] 1.1 **[TDD — Red/Green]** Crear `frontend/src/types/reception.ts` con los tipos estrictos (cero `any`, Regla Dura #4) para `EstadoTurno`, `OrigenTurno`, `ParticipantePacienteResumen`, `ParticipanteOdontologoResumen`, `AgendaTurnoDiaItem`, `TurnoEstadoUpdatePayload`, `PlantillaItem`, `PlantillaCreatePayload` y `PlantillaUpdatePayload` (respetando `extra="forbid"`, Regla Dura #1).
- [x] 1.2 **[TDD — Red/Green/Refactor]** Escribir tests unitarios en `frontend/src/services/__tests__/reception.service.test.ts` e implementar `frontend/src/services/reception.service.ts` cubriendo:
  - `getAgendaDia({ fecha, odontologo_id })` → `GET /api/agenda/dia?fecha=YYYY-MM-DD[&odontologo_id=N]`.
  - `updateTurnoEstado(turnoId, { estado })` → `PATCH /api/turnos/{id}` con body exacto `{ estado }` (`"confirmado"` o `"anulado"`, Reglas Duras #8 y #9).
  - `getPlantillas(odontologo_id?)` → `GET /api/plantillas[?odontologo_id=N]`.
  - `createPlantilla(payload)` → `POST /api/plantillas`.
  - `updatePlantilla(plantillaId, payload)` → `PATCH /api/plantillas/{id}` enviando solo campos editables permitidos.
  - `deletePlantilla(plantillaId)` → `DELETE /api/plantillas/{id}`.

## 2. Hooks de TanStack Query (`useReceptionAgenda.ts` y `usePlantillas.ts`)

- [x] 2.1 **[TDD — Red/Green/Refactor]** Escribir tests en `frontend/src/hooks/__tests__/useReceptionAgenda.test.tsx` e implementar `frontend/src/hooks/useReceptionAgenda.ts` con `useAgendaDiaQuery` y `useUpdateTurnoEstadoMutation` (invalidación automática de `['agenda-dia']`, cero `useEffect` para data fetching según Regla Dura #6).
- [x] 2.2 **[TDD — Red/Green/Refactor]** Escribir tests en `frontend/src/hooks/__tests__/usePlantillas.test.tsx` e implementar `frontend/src/hooks/usePlantillas.ts` con `usePlantillasQuery`, `useCreatePlantillaMutation`, `useUpdatePlantillaMutation` y `useDeletePlantillaMutation` (invalidación automática de `['plantillas']`, cero `useEffect`).

## 3. Vista de Agenda Diaria de Recepción (`RecepcionAgendaPage.tsx`)

- [x] 3.1 **[TDD — Red/Green/Refactor]** Escribir tests de integración de UI en `frontend/src/pages/__tests__/RecepcionAgendaPage.test.tsx` (usando exclusivamente datos sintéticos según Regla Dura #12: `"Lucía Gómez"`, `"Dr. Martín Ruiz"`) cubriendo:
  - Renderizado de agenda diaria por fecha (`YYYY-MM-DD`) y filtro por `odontologo_id` y por estado.
  - Visibilidad explícita de turnos en estado `cancelado` y `origen="online"` con botones de acción deshabilitados (`CB-03`, `US-005 CA-1/CA-2`).
  - Confirmación de turno `solicitado → confirmado` (`PATCH /api/turnos/{id}`).
  - Anulación de turno `solicitado | confirmado → anulado` (`PATCH /api/turnos/{id}`) y visualización de alertas accesibles (`role="alert"`) ante errores `422` (ventana menor a 24 h, `RN-TU-05`), `409` (transición inválida) o `404`/`422` en filtro de odontólogo (`CB-06`).
- [x] 3.2 **[TDD — Green/Refactor]** Implementar `frontend/src/pages/RecepcionAgendaPage.tsx` en `PascalCase` (Regla Dura #5) con selector de fecha local, filtro de odontólogo y estado, badges semánticos de estado y origen, contadores resumen del día y acciones de Confirmar/Anular con estados de carga.

## 4. Vista de Gestión de Plantillas Semanales (`RecepcionPlantillasPage.tsx`)

- [x] 4.1 **[TDD — Red/Green/Refactor]** Escribir tests de integración de UI en `frontend/src/pages/__tests__/RecepcionPlantillasPage.test.tsx` (datos sintéticos) cubriendo:
  - Listado semanal agrupado por día (`0 = Lunes` a `6 = Domingo`) y filtrado por `odontologo_id`.
  - Alta de nueva plantilla (`POST /api/plantillas`) incluyendo bloques contiguos válidos (`hora_fin == hora_inicio`, `CB-01`).
  - Edición parcial de plantilla existente (`PATCH /api/plantillas/{id}`, Regla Dura #9) y eliminación (`DELETE /api/plantillas/{id}`).
  - Exhibición de alerta accesible (`role="alert"`) ante conflicto `409 Conflict` por superposición horaria (`RN-AG-01` / `CB-04`) o `422` por odontólogo inválido (`CB-06`) preservando los datos del formulario.
- [x] 4.2 **[TDD — Green/Refactor]** Implementar `frontend/src/pages/RecepcionPlantillasPage.tsx` en `PascalCase` con formulario accesible de creación/edición parcial, normalización de horas `HH:MM`, vista semanal por día y baja de bloques horarios.

## 5. Integración en Router y Verificación Integral

- [x] 5.1 **[TDD — Red/Green]** Actualizar `frontend/src/router/routes.tsx` y `frontend/src/router/__tests__/routes.test.tsx` para montar `RecepcionAgendaPage` en `/recepcion/agenda` y `RecepcionPlantillasPage` en `/recepcion/plantillas`.
- [x] 5.2 **[Verificación]** Ejecutar la suite completa de Vitest (`npm test -- --run`) y el build de producción (`npm run build`) verificando 0 errores de TypeScript (`strict: true`) y 100% de tests en verde.
