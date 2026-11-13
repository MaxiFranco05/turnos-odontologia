# Spec Delta: odontologo-calendario

## ADDED Requirements

### Requirement: Resumen mensual de turnos del odontólogo en /api/mis-turnos/calendario
El sistema SHALL proveer el endpoint `GET /api/mis-turnos/calendario` para que un usuario autenticado con rol `odontologo` obtenga el resumen diario de sus turnos activos dentro de un mes calendario (`anio`, `mes`) en la zona horaria de la clínica, excluyendo turnos `cancelado` y `anulado`, sin alterar `GET /api/mis-turnos`.

#### Scenario: Consulta exitosa del resumen mensual con días mixtos (Happy Path)
- **WHEN** un odontólogo autenticado solicita `GET /api/mis-turnos/calendario?anio=2026&mes=11` y posee turnos en estado `confirmado`, `solicitado`, `presente` y `ausente` en distintas fechas de noviembre de 2026
- **THEN** el sistema responde HTTP 200 con un listado ordenado ascendentemente únicamente con los días que tienen `total_activos > 0`, desglosando `fecha`, `confirmados`, `solicitados`, `atendidos` (`presente` + `ausente`) y `total_activos`

#### Scenario: Parámetros anio y mes omitidos toman el mes actual de la clínica (CB-05)
- **WHEN** un odontólogo autenticado solicita `GET /api/mis-turnos/calendario` sin especificar `anio` ni `mes`
- **THEN** el sistema resuelve el año y mes vigentes según `TIMEZONE` de la clínica (`America/Argentina/Buenos_Aires`) y retorna los días activos correspondientes a ese mes

#### Scenario: Turnos cancelados o anulados no generan actividad en el calendario (CB-03, RN-TU-04)
- **WHEN** un día del mes contiene exclusivamente turnos en estado `cancelado` o `anulado` para el odontólogo autenticado
- **THEN** ese día no es incluido en el resumen de `GET /api/mis-turnos/calendario` ni suma al conteo de `confirmados`, `solicitados`, `atendidos` o `total_activos`

#### Scenario: Límite mensual en zona horaria clínica sin desfase UTC (CB-01, CB-05)
- **WHEN** el odontólogo tiene un turno iniciado a las `22:00` hora clínica (`America/Argentina/Buenos_Aires`, `01:00Z` del día siguiente en UTC) el último día de un mes
- **THEN** el turno se contabiliza en la fecha local clínica del último día de ese mes y no se desplaza al mes siguiente

#### Scenario: Validación de parámetros inválidos en mes o año (Error de validación)
- **WHEN** un odontólogo solicita `GET /api/mis-turnos/calendario?anio=2026&mes=13` o `mes=0`
- **THEN** el sistema rechaza la petición con HTTP 422

#### Scenario: Control de acceso por rol y aislamiento por odontólogo (CB-06, RN-AU-02, RN-GL-01)
- **WHEN** un usuario autenticado con rol `paciente` o `recepcion` solicita `GET /api/mis-turnos/calendario`
- **THEN** el sistema rechaza la petición con HTTP 403 y además un odontólogo nunca visualiza turnos asignados a otro odontólogo

### Requirement: Indicadores visuales (dots) de turnos en el calendario mensual del odontólogo
La vista mensual de `OdontologoAgendaPage` SHALL consultar el resumen mensual del odontólogo autenticado y renderizar indicadores visuales (dots) diferenciados en cada celda diaria que posea turnos activos, manteniendo la selección manual de fecha y accesibilidad.

#### Scenario: Renderizado de dots por estado en días con turnos (Happy Path)
- **WHEN** el odontólogo abre el calendario mensual y el endpoint retorna días con `confirmados > 0` y otros días con `solicitados > 0`
- **THEN** cada celda diaria correspondiente renderiza el dot esmeralda para turnos confirmados y/o el dot ámbar para turnos solicitados, junto con una leyenda visible y texto accesible indicando las cantidades

#### Scenario: Días sin turnos no muestran dots de turnos y mantienen solo estado de selección/hoy
- **WHEN** un día del mes no figura en el resumen mensual devuelto por el servidor
- **THEN** la celda muestra el número de día sin dots de actividad clínica y conserva únicamente el resaltado visual cuando está seleccionado o es la fecha actual

#### Scenario: Sincronización de dots tras cambio de mes o actualización de asistencia
- **WHEN** el odontólogo navega al mes siguiente/anterior o marca un turno como `presente` o `ausente`
- **THEN** la grilla consulta o invalida la query mensual para ese `(anio, mes)` y refleja los conteos actualizados

### Requirement: Script CLI separado e idempotente para poblar turnos demo del calendario
El proyecto SHALL incluir el script CLI independiente `backend/scripts/seed_calendar_demo.py` que agregue un conjunto acotado de turnos sintéticos en días hábiles del mes actual para poblar visualmente el calendario de odontólogos y pacientes sin modificar `backend/scripts/seed.py`.

#### Scenario: Creación acotada de turnos demo alineados a plantilla y sin solape (RN-AG-01, RN-AG-02, CB-02, CB-04)
- **WHEN** se ejecuta `python -m scripts.seed_calendar_demo` luego de haber ejecutado el seed base (`scripts.seed`)
- **THEN** se crean entre 1 y 2 turnos sintéticos adicionales distribuidos en al menos 3 días hábiles del mes actual repartidos entre ambos odontólogos y ambos pacientes demo, dentro de sus bloques de `PlantillaDisponibilidad` (`30 min`), mezclando estados `confirmado` y `solicitado` y sin superponer horarios existentes

#### Scenario: Re-ejecución idempotente del script demo
- **WHEN** se ejecuta `python -m scripts.seed_calendar_demo` por segunda vez sobre la misma base de datos
- **THEN** no se duplican los turnos demo ya existentes ni se producen errores por solapamiento horario (`RN-AG-01`)
