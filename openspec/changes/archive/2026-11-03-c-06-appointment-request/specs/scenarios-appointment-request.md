# Scenarios: C-06 — Appointment Request (`POST /api/turnos`)

> Escenarios BDD (`Given` / `When` / `Then`) trazables a `specs/appointment-request/spec.md`, `05_reglas_de_negocio.md` (`RN-AG-01`, `RN-AG-02`, `RN-TU-01`, `RN-TU-04`, `RN-GL-01`, `RN-GL-02`), casos de borde `CB-01`..`CB-06` y las 13 Reglas Duras de `AGENTS.md`. Todos los datos son 100% sintéticos ficticios (Regla Dura #12).

---

## 1. Flujo Principal (Happy Path)

### Escenario 1.1: Reserva exitosa en horario libre derivado de plantilla (`201 Created`)
- **Given** la odontóloga sintética `Dra. Sofía Martín` (`id=10`, `rol="odontologo"`) posee una `PlantillaDisponibilidad` para los días lunes (`dia_semana=0`, `hora_inicio="09:00:00"`, `hora_fin="11:00:00"`, `duracion_slot_minutos=30`, `prestacion="Consulta general"`)
- **And** la paciente sintética `Lucía Gómez` (`id=25`, `rol="paciente"`, `debe_cambiar_password=False`) se encuentra autenticada con un JWT válido
- **And** no existen turnos vigentes para `Dra. Sofía Martín` en el slot del próximo lunes `09:30:00-03:00` a `10:00:00-03:00`
- **When** `Lucía Gómez` envía `POST /api/turnos` con payload `{"odontologo_id": 10, "inicio": "<lunes-futuro>T09:30:00-03:00", "fin": "<lunes-futuro>T10:00:00-03:00", "motivo": "Control anual y limpieza"}`
- **Then** el servidor responde con HTTP `201 Created`
- **And** el cuerpo JSON retorna el turno creado con `id` autogenerado, `paciente_id=25`, `odontologo_id=10`, `estado="solicitado"`, `origen="online"`, `motivo="Control anual y limpieza"`
- **And** al consultar posteriormente `GET /api/disponibilidad?odontologo_id=10&fecha=<lunes-futuro>`, el slot `09:30–10:00` ya no se ofrece como disponible (`US-003 CA-3`).

---

## 2. Reglas Anti-Solapamiento y Casos de Borde Horarios (`RN-AG-01`, `CB-01`..`CB-04`)

### Escenario 2.1: Rechazo por solapamiento con turno vigente (`409 Conflict` — `RN-AG-01`, `CB-04`)
- **Given** `Dra. Sofía Martín` (`id=10`) ya tiene un turno en estado `solicitado`, `confirmado`, `presente` o `ausente` en el intervalo `<lunes-futuro> 09:30–10:00`
- **When** otro paciente sintético autenticado `Martín Pérez` (`id=26`, `rol="paciente"`) envía `POST /api/turnos` para `odontologo_id=10` en `<lunes-futuro> 09:30–10:00`
- **Then** el servidor rechaza la operación transaccionalmente con HTTP `409 Conflict` indicando que el horario ya se encuentra ocupado (`RN-AG-01`, Regla Dura #13)
- **And** no se persiste ningún registro duplicado en la tabla `turnos`.

### Escenario 2.2: Reserva permitida sobre slot liberado por turno `cancelado` o `anulado` (`201 Created` — `CB-03`, `RN-TU-04`)
- **Given** `Dra. Sofía Martín` (`id=10`) posee un turno previo en `<lunes-futuro> 09:30–10:00` cuyo estado es `cancelado` (por paciente) o `anulado` (por recepción)
- **When** `Lucía Gómez` envía `POST /api/turnos` para `odontologo_id=10` en `<lunes-futuro> 09:30–10:00` con `motivo="Urgencia por dolor molar"`
- **Then** el servidor acepta la solicitud y responde HTTP `201 Created` con el nuevo turno en `estado="solicitado"` (`CB-03`).

### Escenario 2.3: Reserva permitida en slots contiguos adyacentes `fin_A == inicio_B` (`201 Created` — `CB-01`)
- **Given** `Dra. Sofía Martín` (`id=10`) tiene un turno activo (`confirmado`) en `<lunes-futuro> 09:00–09:30`
- **When** `Lucía Gómez` solicita el slot inmediatamente contiguo `<lunes-futuro> 09:30–10:00` (`fin_A == inicio_B`)
- **Then** el servidor responde HTTP `201 Created` sin falso positivo de solapamiento, tratando los intervalos como semiabiertos `[inicio, fin)` (`CB-01`).

---

## 3. Derivación de Plantilla y Reglas Temporales (`RN-AG-02`, `RN-GL-02`, `CB-02`, `CB-05`)

### Escenario 3.1: Rechazo de horario fuera de la plantilla del profesional (`422 Unprocessable Entity` — `RN-AG-02`)
- **Given** `Dra. Sofía Martín` (`id=10`) atiende únicamente los lunes de `09:00` a `11:00` (`duracion_slot_minutos=30`)
- **When** `Lucía Gómez` solicita un turno para el próximo lunes de `14:00` a `14:30` (o para un martes donde no existe plantilla)
- **Then** el servidor responde HTTP `422 Unprocessable Entity` indicando que el horario solicitado no corresponde a un bloque válido de la agenda del odontólogo (`RN-AG-02`).

### Escenario 3.2: Rechazo de slot desalineado o en remanente incompleto de plantilla (`422 Unprocessable Entity` — `CB-02`)
- **Given** `Dra. Sofía Martín` (`id=10`) tiene una plantilla los miércoles de `09:00` a `10:00` con `duracion_slot_minutos=40` (generando solo el slot completo `09:00–09:40`)
- **When** `Lucía Gómez` intenta reservar el remanente `09:40–10:00` (20 min), un bloque desfasado `09:10–09:50`, o un bloque de 60 min `09:00–10:00`
- **Then** el servidor rechaza la solicitud con HTTP `422 Unprocessable Entity` (`CB-02`).

### Escenario 3.3: Rechazo de solicitud en fecha pasada o en slot ya transcurrido hoy (`422 Unprocessable Entity` — `RN-GL-02`, `CB-05`)
- **Given** el reloj del consultorio en `TIMEZONE=America/Argentina/Buenos_Aires` marca lunes `10:15:00-03:00`
- **When** `Lucía Gómez` envía `POST /api/turnos` para una fecha anterior a hoy o para el slot de hoy `10:00–10:30` (`inicio <= ahora`)
- **Then** el servidor rechaza la solicitud con HTTP `422 Unprocessable Entity` (`RN-GL-02`, `CB-05`).

---

## 4. Validación de Profesional, Autorización RBAC y Payload (`RN-TU-01`, `RN-GL-01`, `CB-06`, Regla Dura #1)

### Escenario 4.1: Odontólogo inexistente (`404 Not Found`) o usuario sin rol odontólogo (`422 Unprocessable Entity` — `CB-06`)
- **Given** `Lucía Gómez` está autenticada como `paciente`
- **When** envía `POST /api/turnos` con `odontologo_id=99999` (inexistente)
- **Then** el servidor responde HTTP `404 Not Found`
- **And** cuando envía `POST /api/turnos` con `odontologo_id` perteneciente a un usuario con `rol="recepcion"` o `rol="paciente"`
- **Then** el servidor responde HTTP `422 Unprocessable Entity` (`CB-06`).

### Escenario 4.2: Rechazo de roles no autorizados o contraseña temporal pendiente (`403 Forbidden` — `RN-TU-01`, `RN-GL-01`, `US-010`)
- **Given** un usuario autenticado con `rol="recepcion"`, `rol="odontologo"`, o un `paciente` con `debe_cambiar_password=True`
- **When** intenta ejecutar `POST /api/turnos`
- **Then** el servidor responde HTTP `403 Forbidden` sin efectos colaterales en la base de datos.

### Escenario 4.3: Validación estricta de payload Pydantic (`422 Unprocessable Entity` — Regla Dura #1)
- **Given** `Lucía Gómez` está autenticada como `paciente`
- **When** envía `POST /api/turnos` con campos no declarados (ej. `"paciente_id": 99`, `"estado": "confirmado"`, `"box": 1`), con `motivo: "   "` (vacío tras strip), o con `fin <= inicio`
- **Then** el servidor rechaza el payload en el borde HTTP con `422 Unprocessable Entity` (`ConfigDict(extra="forbid", str_strip_whitespace=True)`).
