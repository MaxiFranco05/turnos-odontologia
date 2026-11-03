# frontend-reception-portal Specification

## Purpose
Provee las interfaces operativas del portal de recepción (`/recepcion/agenda` y `/recepcion/plantillas`), permitiendo consultar la agenda clínica diaria por fecha y odontólogo, confirmar o anular turnos respetando las transiciones y la ventana de anticipación mínima de 24 horas, y administrar las plantillas semanales de disponibilidad sin solapamientos horarios.

## Requirements

### Requirement: Daily clinic agenda display and filtering (US-005)
The reception agenda screen (`/recepcion/agenda`) MUST query `GET /api/agenda/dia` with a required `fecha` (`YYYY-MM-DD`) and optional `odontologo_id`, rendering each appointment's time range, patient details (`nombre`, `nro_socio`, `email`), dentist name, reason, booking origin (`online` or `recepcion`), and lifecycle state (`solicitado`, `confirmado`, `anulado`, `cancelado`, `presente`, `ausente`), including patient cancellations (`RN-GL-01`, `RN-TU-02`).

#### Scenario: Consulta exitosa de agenda diaria global y filtrado por odontólogo (Expected Behavior)
- **GIVEN** un usuario autenticado con rol `recepcion` en la pantalla `/recepcion/agenda`
- **WHEN** selecciona la fecha `"2026-11-20"` y opcionalmente filtra por el odontólogo sintético `"Dr. Martín Ruiz"` (`odontologo_id=2`)
- **THEN** la interfaz consulta `GET /api/agenda/dia?fecha=2026-11-20&odontologo_id=2` y muestra la lista ordenada cronológicamente con horario, paciente (`"Lucía Gómez"`, socio `"SOC-1001"`), odontólogo, motivo, badge de origen y badge de estado

#### Scenario: Visibilidad explícita de turnos cancelados por el paciente y origen online (Edge Case — CB-03 / US-005 CA-1, CA-2)
- **GIVEN** una fecha operativa en `/recepcion/agenda` que incluye un turno previamente cancelado por la paciente sintética `"Lucía Gómez"` con `estado="cancelado"` y `origen="online"`
- **WHEN** la pantalla renderiza el listado de turnos del día
- **THEN** el turno permanece visible en la grilla histórica del día con el badge semántico `"Cancelado"` y el indicador de origen `"Online"`, deshabilitando las acciones de confirmación o anulación sobre ese registro

#### Scenario: Manejo de error al filtrar por un odontólogo inexistente o usuario sin rol odontólogo (Business Error — CB-06)
- **GIVEN** un usuario de recepción en `/recepcion/agenda` aplicando un filtro por `odontologo_id`
- **WHEN** el backend responde con código HTTP `404 Not Found` (ID inexistente) o `422 Unprocessable Entity` (el usuario no posee rol `odontologo` según `CB-06`)
- **THEN** la interfaz muestra una alerta accesible describiendo el error devuelto por la API y permite restablecer el filtro para volver a ver la agenda completa

### Requirement: Appointment confirmation and annulment actions (US-005, RN-TU-02, RN-TU-05)
The reception agenda screen MUST allow confirming appointments in state `solicitado` (`PATCH /api/turnos/{id}` with `{ "estado": "confirmado" }`) and annulling appointments in state `solicitado` or `confirmado` (`PATCH /api/turnos/{id}` with `{ "estado": "anulado" }`), refreshing the agenda upon success and displaying domain errors when the 24-hour anticipation window (`RN-TU-05`) or state machine rules are violated.

#### Scenario: Confirmación exitosa de un turno solicitado desde recepción (Expected Behavior)
- **GIVEN** un turno en estado `solicitado` perteneciente a la paciente sintética `"Lucía Gómez"` en `/recepcion/agenda`
- **WHEN** el recepcionista acciona el botón `"Confirmar"` sobre dicho turno
- **THEN** la aplicación envía `PATCH /api/turnos/{id}` con payload exacto `{ "estado": "confirmado" }`, invalida la caché de la agenda diaria tras recibir `200 OK` y actualiza el badge del turno a `"Confirmado"`

#### Scenario: Anulación exitosa de un turno con más de 24 horas de anticipación (Expected Behavior)
- **GIVEN** un turno en estado `solicitado` o `confirmado` cuyo inicio supera las 24 horas respecto al reloj del servidor
- **WHEN** el recepcionista selecciona `"Anular"` y confirma la acción
- **THEN** la aplicación envía `PATCH /api/turnos/{id}` con `{ "estado": "anulado" }` y actualiza la fila al estado `"Anulado"`

#### Scenario: Rechazo de anulación por ventana menor a 24 horas o conflicto de estado (Business Error — RN-TU-05)
- **GIVEN** un turno en `/recepcion/agenda` que se intenta anular con menos de 24 horas de anticipación o que ya cambió de estado en otra sesión
- **WHEN** el backend responde con HTTP `422 Unprocessable Entity` (`AnticipationWindowError`) o HTTP `409 Conflict` (`InvalidStateTransitionError`)
- **THEN** la interfaz preserva el estado actual en pantalla y exhibe una alerta accesible (`role="alert"`) con el detalle del motivo de rechazo informado por el servidor

### Requirement: Weekly availability templates CRUD management (US-006, RN-AG-01)
The reception templates screen (`/recepcion/plantillas`) MUST allow viewing (`GET /api/plantillas`), creating (`POST /api/plantillas`), partially updating (`PATCH /api/plantillas/{id}`), and deleting (`DELETE /api/plantillas/{id}`) weekly availability blocks per dentist (`dia_semana` 0 to 6, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`, `prestacion`), surfacing HTTP `409` overlap conflicts (`RN-AG-01`, `CB-04`) while permitting adjacent time blocks (`CB-01`).

#### Scenario: Creación y edición parcial exitosa de una plantilla horaria (Expected Behavior)
- **GIVEN** un usuario de recepción en `/recepcion/plantillas` gestionando la agenda del odontólogo sintético `"Dr. Martín Ruiz"` (`odontologo_id=2`)
- **WHEN** completa el formulario de alta con `dia_semana=0` (Lunes), `hora_inicio="08:00"`, `hora_fin="12:00"`, `duracion_slot_minutos=30` y `prestacion="Consulta general"` (o edita parcialmente una plantilla existente mediante `PATCH /api/plantillas/{id}`)
- **THEN** la aplicación envía el payload estricto sin campos extra, recibe `201 Created` (o `200 OK` en edición), refresca el listado semanal y muestra el bloque bajo el día `"Lunes"`

#### Scenario: Rechazo por superposición parcial o total de horario para el mismo odontólogo y día (Business Error — RN-AG-01 / CB-04)
- **GIVEN** una plantilla existente los Lunes de `08:00` a `12:00` para `"Dr. Martín Ruiz"`
- **WHEN** recepción intenta crear o editar otra plantilla el mismo Lunes de `10:00` a `14:00` y el backend responde `409 Conflict`
- **THEN** la interfaz mantiene abierto el formulario sin perder los datos ingresados y muestra una alerta accesible indicando que el bloque horario se superpone con una plantilla existente

#### Scenario: Registro válido de bloques horarios contiguos o adyacentes y eliminación de plantilla (Edge Case — CB-01)
- **GIVEN** una plantilla existente los Lunes de `08:00` a `12:00` para `"Dr. Martín Ruiz"`
- **WHEN** recepción crea un segundo bloque contiguo de `12:00` a `16:00` (`hora_fin == hora_inicio`, `CB-01`) o elimina un bloque existente mediante `"Eliminar"` (`DELETE /api/plantillas/{id}` → `204 No Content`)
- **THEN** el sistema acepta el bloque contiguo sin error de solapamiento y, en caso de baja, remueve inmediatamente el bloque del listado semanal
