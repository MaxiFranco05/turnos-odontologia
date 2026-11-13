# Design: C-22 Indicadores Mensuales (Dots) en Calendario del Odontólogo y Seed Demo

## Context

Ver [`proposal.md`](./proposal.md) para la motivación. Estado actual relevante:
- `GET /api/mis-turnos` en [`backend/app/api/mis_turnos.py`](../../backend/app/api/mis_turnos.py) impone consulta por `fecha` única para `RolUsuario.ODONTOLOGO` y rechaza explícitamente `fecha_desde` / `fecha_hasta` con HTTP 422 (cubierto por los tests de C-09).
- `SqlAlchemyTurnoRepository.find_by_dentist_range(odontologo_id, start, end)` en [`backend/app/infrastructure/repositories/turno.py`](../../backend/app/infrastructure/repositories/turno.py) ya implementa la consulta SQLAlchemy 2.0 `select()` (Regla Dura #2) sobre el índice `(odontologo_id, inicio)`.
- `backend/scripts/seed.py` y `backend/app/infrastructure/seed.py` (C-16) fijan 5 usuarios, 20 plantillas horarias (`09:00–13:00` y `14:00–18:00`, slots de 30 min, lunes a viernes) y exactamente 4 turnos iniciales validados por `test_seed_script.py`.

## Goals / Non-Goals

**Goals:**
- Exponer un resumen mensual liviano y por odontólogo autenticado (`GET /api/mis-turnos/calendario`) sin romper contratos de C-09.
- Mantener la lógica de límites de mes y agregación diaria en helpers puros sincrónicos dentro de `backend/app/application/turnos.py` (Regla Dura #3) usando `ZoneInfo(TIMEZONE)`.
- Mostrar dots diferenciados en la grilla mensual de `OdontologoAgendaPage.tsx` usando TanStack Query (Regla Dura #6) y tipado estricto (Regla Dura #4).
- Proveer un script CLI separado (`seed_calendar_demo.py`) que sume turnos sintéticos adicionales (Regla Dura #12) validando bloques de plantilla y no superposición (`RN-AG-01`, `RN-AG-02`, Regla Dura #13).

**Non-Goals:**
- No se agregan columnas ni migraciones Alembic al esquema de base de datos.
- No se modifica el comportamiento ni los datos base de `backend/scripts/seed.py`.
- No se habilitan consultas de calendario de otros odontólogos (aislamiento BOLA estricto por `current_user.id`, `RN-AU-02`).

## Decisions

### 1. Nuevo sub-recurso `GET /api/mis-turnos/calendario` vs. modificar `GET /api/mis-turnos`
- **Decisión**: Crear `GET /api/mis-turnos/calendario?anio={anio}&mes={mes}` en `backend/app/api/mis_turnos.py` restringido a `RolUsuario.ODONTOLOGO` vía `require_roles(RolUsuario.ODONTOLOGO)`.
- **Alternativa descartada**: Aceptar `fecha_desde`/`fecha_hasta` para odontólogos en `GET /api/mis-turnos`. Rompería los tests existentes de C-09 que validan el rechazo 422 y mezclaría listas detalladas de pacientes con un agregado liviano de calendario.
- **Contrato y Reglas Duras**:
  - URI basada en sustantivo (Regla Dura #8).
  - Query params opcionales `anio: int | None = Query(default=None, ge=2000, le=2100)` y `mes: int | None = Query(default=None, ge=1, le=12)`. Si faltan, se toma la fecha actual en `ZoneInfo(settings.TIMEZONE)` (`CB-05`).
  - Schemas Pydantic con `ConfigDict(extra="forbid")` (Regla Dura #1):
    - `CalendarioDiaResumenResponse(fecha: datetime.date, confirmados: int, solicitados: int, atendidos: int, total_activos: int)`
    - `CalendarioMesResponse(anio: int, mes: int, dias: list[CalendarioDiaResumenResponse])`
  - Seguridad / RBAC (`RN-AU-02`, `RN-GL-01`, `CB-06`): Solo `RolUsuario.ODONTOLOGO` recibe 200; `paciente` y `recepcion` reciben 403; el filtro siempre usa `odontologo_id=current_user.id` (sin parámetro `odontologo_id` arbitrario).

### 2. Helpers puros sincrónicos en `backend/app/application/turnos.py` (Regla Dura #3)
- **Decisión**: Implementar dos funciones puras sincrónicas (`def`, no `async def`):
  1. `get_clinic_month_bounds(anio: int, mes: int, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]`:
     - Calcula `[primer_dia_00:00, primer_dia_mes_siguiente_00:00)` con `ZoneInfo`, usando `calendar.monthrange` o desplazamiento al día 1 del mes siguiente (manejando diciembre → enero del año siguiente).
  2. `summarize_dentist_month_appointments(turnos: list[Turno], anio: int, mes: int, timezone_str: str | None = None) -> list[dict[str, int | datetime.date]]`:
     - Convierte `turno.inicio` con `.astimezone(tz).date()` para atribuir el turno al día calendario local de la clínica (`CB-05`, evitando desfases UTC nocturnos).
     - Excluye turnos cuyo `estado` sea `EstadoTurno.CANCELADO` o `EstadoTurno.ANULADO` (`CB-03`, `RN-TU-04`).
     - Filtra por `(local_date.year == anio and local_date.month == mes)` por seguridad ante turnos que crucen medianoche en bordes de mes (`CB-01`).
     - Agrupa por fecha ordenando ascendentemente y clasifica:
       - `confirmados`: `EstadoTurno.CONFIRMADO`
       - `solicitados`: `EstadoTurno.SOLICITADO`
       - `atendidos`: `EstadoTurno.PRESENTE` o `EstadoTurno.AUSENTE`
       - `total_activos = confirmados + solicitados + atendidos`
     - Omite días con `total_activos == 0`.

### 3. Integración Frontend con TanStack Query y Grilla de Dots
- **Decisión**:
  - En `frontend/src/services/dentist.service.ts`: agregar interfaces estrictas `CalendarioDiaResumen`, `CalendarioMesResponse` (Regla Dura #4) y función `getMisTurnosCalendario(anio: number, mes: number)` que invoca `GET /mis-turnos/calendario` con `{ params: { anio, mes } }`.
  - En `frontend/src/hooks/useDentistAgenda.ts`: agregar `useDentistCalendarQuery(anio: number, mes: number)` con `queryKey: ['dentist-calendar', { anio, mes }]` (Regla Dura #6, sin `useEffect`). Actualizar `useUpdateAsistenciaMutation` para invalidar también `['dentist-calendar']` junto a `['dentist-agenda']` y `['agenda-dia']`.
  - En `frontend/src/pages/OdontologoAgendaPage.tsx`: derivar `activeYear = calendarMonth.getFullYear()` y `activeMonth = calendarMonth.getMonth() + 1`, mapear `dias` por `fecha` (`Record<string, CalendarioDiaResumen>`) y renderizar por celda:
    - Hasta 3 indicadores compactos debajo del número del día (solo si `resumen` existe): dot esmeralda (`bg-emerald-400` / contrastado en seleccionado) si `confirmados > 0`, dot ámbar (`bg-amber-400`) si `solicitados > 0` y dot cian/pizarra (`bg-sky-400` / `bg-zinc-400`) si `atendidos > 0 && confirmados === 0 && solicitados === 0` (o mostrar ambos `confirmados` + `solicitados` si coexisten).
    - El estado seleccionado deja de depender de un dot negro ambiguo y se destaca por fondo/borde del botón, mientras los dots reflejan exclusivamente turnos del calendario.
    - Añadir leyenda mínima (`Confirmados` / `Pend. recepción` / `Atendidos`) y `aria-label` descriptivo por botón de fecha.

### 4. Script CLI separado e idempotente `seed_calendar_demo.py`
- **Decisión**: Crear `backend/app/infrastructure/seed_calendar_demo.py` + wrapper CLI `backend/scripts/seed_calendar_demo.py`, separado de `backend/scripts/seed.py`.
- **Alternativa descartada**: Agregar los turnos extras dentro de `seed.py`. Rompería la aserción exacta `count == 4` de `test_seed_script.py` (C-16) y mezclaría fixture mínima de contrato con datos visuales de demo.
- **Lógica de generación segura**:
  - Busca los usuarios sembrados por `seed.py` (odontólogos `sofia.martin@turnosodontologia.com`, `lucas.garcia@turnosodontologia.com` y pacientes `carlos.benitez@example.com`, `lucia.gomez@example.com`) y sus bloques de `PlantillaDisponibilidad` (`dia_semana`, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`). Si faltan usuarios/plantillas base, falla con mensaje claro sugiriendo correr `python -m scripts.seed`.
  - Selecciona una ventana acotada de días hábiles del mes actual (ej. +1, +2, +3, +5 días hábiles dentro del mes actual — o días hábiles previos/posteriores del mismo mes si hoy es fin de mes) creando ~6–8 turnos sintéticos en total (máx. 1–2 turnos por día por odontólogo, nunca saturando la grilla):
    - Repartidos entre ambos odontólogos (`Sofía Martín` y `Lucas García`) y ambos pacientes (`Carlos Benítez` y `Lucía Gómez`), todos sintéticos (Regla Dura #12).
    - Incluye mayoría en estado `confirmado` (para que aparezcan inmediatamente en el calendario del odontólogo y puedan marcarse `presente`/`ausente` si corresponden) y algunos en `solicitado` (para visualizar el dot ámbar pendiente de recepción y poder confirmarlos en demo).
  - **Validación estricta de reglas de agenda**:
    - Cada horario `inicio` / `fin` se calcula a partir de un slot real de `PlantillaDisponibilidad` (`30 min`, `RN-AG-02`, `CB-02`).
    - Antes de insertar, consulta turnos activos existentes (`estado NOT IN ('cancelado', 'anulado')`) en esa ventana para garantizar **idempotencia** (si ya existe un turno para el mismo `(odontologo_id, inicio)`, lo omite) y **cero solapamiento** (`inicio < existente.fin and fin > existente.inicio`, `RN-AG-01`, `CB-04`, Regla Dura #13).
    - Nota sobre `sillon` de Regla Dura #13: en el modelo de datos actual v1 (`Turno`), cada odontólogo opera su propia agenda exclusiva sin columna separada de `sillon`; validar no superposición por `odontologo_id` y no duplicar turnos activos cubre la invariante `RN-AG-01` en v1.

## Risks / Trade-offs

- **Fin de mes con pocos días hábiles restantes**: Si el usuario corre `seed_calendar_demo.py` el último día hábil del mes, buscar solo `hoy + N` cruzaría al mes siguiente → *Mitigación*: Priorizar días hábiles futuros dentro del mismo `(anio, mes)` actual (`>= hoy` si existen) y, si faltan para completar al menos 3 días distintos en el mes actual, completar con otros días hábiles del mismo mes (asegurando cumplir idempotencia y evitando solapes). Nota: como `seed_calendar_demo.py` inserta registros demo directamente en DB (análogo a `seed.py`) y no pasa por `POST /api/turnos` de paciente (`RN-GL-02`), puede crear registros de ejemplo dentro del mismo mes si hoy es fin de mes, pero por defecto elige días hábiles futuros `>= hoy` cuando estén dentro del mes.
- **Desfase visual entre días con `solicitado` y lista de `confirmadosDelDia` en vista `/odontologo/calendario`**: Si un día tiene solo dot ámbar (`solicitado`) y el odontólogo hace clic en vista `/odontologo/calendario`, la lista inferior dice que no hay turnos confirmados por Recepción → *Mitigación*: En la leyenda del calendario y el `aria-label` del día se distingue claramente `Confirmados` (esmeralda) vs. `Pendientes de Recepción` (ámbar), evitando confusión al usuario.

## UI Mockups

Decision: no (project policy)
