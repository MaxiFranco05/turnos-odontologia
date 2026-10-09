# Reglas de Negocio

Cada regla tiene un código único `RN-{DOMINIO}-{NN}` para trazabilidad.
Dominios: AU (autenticación), TU (turnos), AG (agenda/disponibilidad), GL
(globales).

## Dominio: Autenticación (RN-AU)

- **RN-AU-01**: el paciente inicia sesión con correo **o** N.º de
  socio/afiliado + contraseña. — Decidido en Discovery; admite ambos
  identificadores.
- **RN-AU-02**: las vistas y acciones se filtran por rol en el servidor; el
  odontólogo solo opera sobre SUS turnos.

## Dominio: Turnos (RN-TU)

- **RN-TU-01**: el paciente solo puede **solicitar** turnos y avisar
  ausentismo sobre los propios; nunca confirma ni anula. — Separa
  autogestión de validación administrativa.
- **RN-TU-02**: solo recepción **confirma** y **anula** turnos.
- **RN-TU-03**: el odontólogo solo marca **presente/ausente** sobre SUS
  turnos.
- **RN-TU-04**: el paciente puede **cancelar** un turno propio, liberando
  el horario. La cancelación del paciente usa el estado `cancelado`; la de
  recepción usa `anulado`: el estado conserva quién ejecutó la acción.
- **RN-TU-05**: la cancelación/anulación exige una anticipación mínima de
  **24 horas** (valor configurable, `CANCEL_MIN_HOURS`).

## Dominio: Agenda / Disponibilidad (RN-AG)

- **RN-AG-01**: un odontólogo no puede tener dos turnos superpuestos. Es
  invariante de **servidor** (constraint + validación transaccional), nunca
  solo validación de cliente. — Diferencial del proyecto: ningún competidor
  relevado la publica como invariante verificable.
- **RN-AG-02**: la disponibilidad reservable deriva de la plantilla del
  odontólogo (días, horarios, duración por prestación), no de carga manual
  turno por turno. — Ver supuesto SU-01 en
  `09_decisiones_y_supuestos.md`.

## Dominio: Excepciones globales

- **RN-GL-01**: toda transición de estado fuera del rol autorizado se
  rechaza con error de autorización, sin efectos colaterales.
- **RN-GL-02**: no se pueden solicitar turnos en horarios pasados (regla
  inferida; validar con el consultorio).
