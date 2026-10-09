# Modelo de Datos

## Dominios

- **Usuarios**: cuentas con rol (paciente, recepción, odontólogo).
- **Agenda / Disponibilidad**: plantillas por odontólogo de las que derivan
  los huecos reservables.
- **Turnos**: reservas con máquina de estados y transiciones por rol.

## ERD (textual)

```
Usuario (1) ──< Turno >── (1) Usuario [como odontólogo]
   │                       │
   │ rol=Paciente           │ rol=Odontólogo
   │
PlantillaDisponibilidad >── (1) Usuario [rol=Odontólogo]

Turno.estado ∈ {solicitado, confirmado, anulado, cancelado, presente, ausente}
(`cancelado` = aviso del paciente; `anulado` = anulación de recepción)
```

## Entidades

### Usuario

- Atributos: `id` (PK), `nombre` (texto), `email` (único, nullable),
  `nro_socio` (único, nullable), `password_hash`, `debe_cambiar_password`
  (bool, para contraseñas temporales de alta por recepción),
  `perfil_completo` (bool, datos sensibles cargados por el paciente),
  `rol` (enum: paciente | recepcion | odontologo), `creado_en`.
- Relaciones: 1—N con Turno como paciente; 1—N con Turno como odontólogo;
  1—N con PlantillaDisponibilidad (solo rol odontólogo).
- Constraints: al menos uno entre `email` y `nro_socio` es obligatorio
  (login admite cualquiera de los dos); `rol` inmutable salvo proceso
  administrativo a definir.

### PlantillaDisponibilidad

- Atributos: `id` (PK), `odontologo_id` (FK → Usuario), `dia_semana`
  (0–6), `hora_inicio`, `hora_fin`, `duracion_slot_minutos`,
  `prestacion` (texto descriptivo del tipo de consulta, definido por
  recepción — sin catálogo fijo en v1).
- Relaciones: N—1 con Usuario (odontólogo).
- Constraints: `hora_fin > hora_inicio`; `duracion_slot_minutos > 0`.

### Turno

- Atributos: `id` (PK), `paciente_id` (FK → Usuario),
  `odontologo_id` (FK → Usuario), `inicio` (timestamp),
  `fin` (timestamp), `motivo` (texto: tipo de consulta descrito por el
  paciente al solicitar), `estado` (enum), `origen` (online | manual),
  `creado_en`, `actualizado_en`.
- Relaciones: N—1 con Usuario (paciente); N—1 con Usuario (odontólogo).
- Constraints:
  - Anti-solape por odontólogo: no pueden existir dos turnos no anulados
    del mismo odontólogo con rangos `[inicio, fin)` intersectados
    (invariante de servidor, RN-AG-01).
  - `fin > inicio`; la duración respeta el slot de la plantilla vigente.
  - Transiciones de `estado` solo según matriz por rol (RN-TU-01…04).
- Índices relevantes: `(odontologo_id, inicio)` para agenda del día y
  chequeo de solape; `(paciente_id, inicio)` para «mis turnos».

## Seed data inicial

Estructura requerida al arrancar (valores: a cargar por el consultorio, sin
datos ficticios precargados):

- Catálogo de estados de turno con sus transiciones permitidas por rol.
- Al menos una cuenta de recepción y las cuentas de odontólogos de la prueba
  inicial (cantidad a definir, ver `10_preguntas_abiertas.md`).
- Valor de anticipación mínima de cancelación (RN-TU-05).
- Plantillas de disponibilidad iniciales por odontólogo.
