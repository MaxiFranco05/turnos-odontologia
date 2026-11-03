# Design: Reception Features (C-14)

## Context

El shell de aplicación (`C-11`) y el flujo de autenticación (`C-12`) ya proveen navegación protegida por rol hacia `/recepcion/agenda` y `/recepcion/plantillas`, además del cliente HTTP centralizado (`apiClient` en `frontend/src/lib/api-client.ts`) con inyección automática de `Authorization: Bearer <token>` y manejo tipado de errores (`ApiError`). En el backend ya se encuentran productivos y testeados los endpoints de `C-05` (`GET/POST/PATCH/DELETE /api/plantillas`), `C-07` (`PATCH /api/turnos/{id}`) y `C-08` (`GET /api/agenda/dia`). Ver `proposal.md` para la motivación funcional.

## Goals / Non-Goals

**Goals:**
- Implementar `RecepcionAgendaPage` (`/recepcion/agenda`) y `RecepcionPlantillasPage` (`/recepcion/plantillas`) siguiendo las 13 Reglas Duras del proyecto (`strict: true`, cero `any`, componentes `PascalCase`, TanStack Query sin `useEffect` para data fetching, URIs basadas en sustantivos y `PATCH` para actualizaciones parciales).
- Alinear los contratos de peticiones frontend con los schemas Pydantic `extra="forbid"` del backend real (`TurnoEstadoUpdate`, `PlantillaCreate`, `PlantillaUpdate`).
- Garantizar feedback accesible (`role="alert"`, estados de carga y deshabilitación en curso) para las reglas de negocio de agenda (`RN-AG-01`, `RN-TU-02`, `RN-TU-05`, `RN-GL-01`) y los casos de borde (`CB-01`, `CB-03`, `CB-04`, `CB-06`).

**Non-Goals:**
- Alta de turnos desde recepción (fuera del alcance de `C-14`; la solicitud de turnos corresponde al portal de paciente en `C-13` / `C-06`).
- Marcado de asistencia `presente` / `ausente` (exclusivo del rol `odontologo` en `C-15` / `C-09`).
- Modificación de endpoints backend existentes.

## Decisions

### 1. Corrección de contrato REST para confirmar y anular turnos (`PATCH /api/turnos/{id}`)
- **Decisión**: Consumir `PATCH /api/turnos/{id}` enviando `{ "estado": "confirmado" }` o `{ "estado": "anulado" }` en lugar de los sub-paths con verbos `PATCH /confirmar` y `PATCH /anular` que figuraban en el texto descriptivo inicial de `CHANGES.md`.
- **Racional**: El backend real (`backend/app/api/turnos.py`) implementó el endpoint unificado `PATCH /api/turnos/{turno_id}` con `TurnoEstadoUpdate(extra="forbid")` en estricto cumplimiento de las **Reglas Duras #8 (NUNCA verbos en paths)** y **#9 (PATCH para updates parciales)**.
- **Alternativas descartadas**: Invocar `/api/turnos/{id}/confirmar` produciría `404 Not Found` contra el backend productivo y violaría la Regla Dura #8.

### 2. Gestión de estado servidor con TanStack Query (`useQuery` + `useMutation`) sin `useEffect`
- **Decisión**: Encapsular todas las lecturas y mutaciones en dos módulos de hooks declarativos:
  - `useReceptionAgenda.ts`:
    - `useAgendaDiaQuery({ fecha, odontologoId })` con `queryKey: ['agenda-dia', fecha, odontologoId ?? 'all']`.
    - `useUpdateTurnoEstadoMutation()` que ejecuta `PATCH /api/turnos/{id}` y en `onSuccess` invalida `['agenda-dia']`.
  - `usePlantillas.ts`:
    - `usePlantillasQuery(odontologoId)` con `queryKey: ['plantillas', odontologoId ?? 'all']`.
    - `useCreatePlantillaMutation()`, `useUpdatePlantillaMutation()` y `useDeletePlantillaMutation()`, invalidando `['plantillas']` tras cada mutación exitosa.
- **Racional**: Cumple la **Regla Dura #6 (NUNCA `useEffect` para data fetching)**, evita condiciones de carrera al cambiar rápidamente la fecha o el odontólogo filtrado, y mantiene sincronizada la UI tras cada confirmación, anulación o cambio de plantilla.

### 3. Cumplimiento estricto de `extra="forbid"` en payloads de mutación
- **Decisión**: Construir constructores de payload explícitos en `reception.service.ts`:
  - `updateTurnoEstado(turnoId, { estado })` envía únicamente `{ estado }`.
  - `createPlantilla(payload)` envía exactamente `{ odontologo_id, dia_semana, hora_inicio, hora_fin, duracion_slot_minutos, prestacion }`.
  - `updatePlantilla(plantillaId, payload)` envía únicamente los campos editables permitidos por `PlantillaUpdate` (`dia_semana`, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`, `prestacion`), omitiendo `id` y `odontologo_id` que son inmutables en `PATCH /api/plantillas/{id}`.
- **Racional**: Cumple la **Regla Dura #1 (`extra="forbid"`)**; si el frontend enviara `id` u `odontologo_id` dentro del body del `PATCH`, FastAPI/Pydantic rechazaría la petición con `422 Unprocessable Entity`.

### 4. Selección y filtrado por Odontólogo sin acoplamiento a endpoints inexistentes
- **Decisión**: Proveer en `RecepcionAgendaPage` y `RecepcionPlantillasPage` un selector/input numérico accesible de `odontologo_id` combinado con sugerencias dinámicas extraídas de los odontólogos conocidos en las respuestas de agenda/plantillas (y opción `"Todos los odontólogos"` para limpiar el filtro), permitiendo ingresar o elegir cualquier ID válido de odontólogo.
- **Racional**: El backend actual (`main.py`) expone `/api/agenda/dia` y `/api/plantillas` con parámetro `odontologo_id: int | None`, sin un endpoint separado `GET /api/odontologos`. Un control híbrido (selector rápido + filtro por ID de odontólogo) permite tanto filtrar por cualquier `odontologo_id` como validar los escenarios de error `404` / `422` (`CB-06`) exigidos por el dominio.

## UI Mockups

Decision: no (project policy)

## Risks / Trade-offs

- **[Risk] Formato de hora `HH:MM:SS` devuelto por PostgreSQL/FastAPI vs inputs HTML `<input type="time">` (`HH:MM`)** → **Mitigación**: Normalizar las cadenas `hora_inicio` y `hora_fin` a `HH:MM` al hidratar el formulario de edición y al renderizar badges horarios en la tabla de plantillas.
- **[Risk] Desfase de fecha por zona horaria UTC en `new Date().toISOString().slice(0, 10)` tarde a la noche en Argentina (`UTC-3`)** → **Mitigación**: Calcular la fecha inicial por defecto utilizando componentes locales (`getFullYear()`, `getMonth() + 1`, `getDate()`) formateados como `YYYY-MM-DD`.
- **[Risk] Intento de anular turnos fuera de la ventana de 24 horas (`RN-TU-05`)** → **Mitigación**: Capturar `ApiError` en `useUpdateTurnoEstadoMutation` y renderizar el mensaje `detail` devuelto por el backend (`422` / `409`) en un banner accesible `role="alert"` sin desmontar la tabla.
