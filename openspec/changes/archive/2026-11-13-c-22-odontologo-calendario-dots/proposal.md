## Why

En el portal del odontólogo (`OdontologoAgendaPage.tsx`), la grilla del calendario mensual solo marca actualmente el día seleccionado, sin mostrar qué días del mes tienen turnos confirmados o solicitados pendientes. Como `GET /api/mis-turnos` acepta únicamente una `fecha` puntual para el rol `odontologo` (rechazando rangos `fecha_desde`/`fecha_hasta` según el contrato de C-09), el profesional debe ir clicando día por día para descubrir dónde tiene pacientes agendados.

Además, el script canónico `backend/scripts/seed.py` (C-16) fija exactamente 4 turnos iniciales y sus tests de integración validan esa cantidad exacta. Para que la vista mensual con indicadores (dots) sea visualmente representativa al probar o demostrar el sistema —con turnos repartidos en distintos días y usuarios sin saturar la agenda ni romper C-16— se necesita un script CLI separado e idempotente.

## What Changes

1. **Nuevo endpoint mensual para odontólogos (`GET /api/mis-turnos/calendario`)**:
   - Recurso basado en sustantivos (Regla Dura #8) en `backend/app/api/mis_turnos.py`, protegido por RBAC para `RolUsuario.ODONTOLOGO` (`require_roles`).
   - Recibe `anio` (int, por defecto año actual en `TIMEZONE` clínica) y `mes` (`1..12`, por defecto mes actual en `TIMEZONE` clínica), reutilizando `SqlAlchemyTurnoRepository.find_by_dentist_range` y helpers puros sincrónicos en `backend/app/application/turnos.py`.
   - Devuelve un resumen diario con `fecha`, `confirmados`, `solicitados` y `total_activos` para cada día del mes con actividad vigente, excluyendo turnos `cancelado` o `anulado` (que liberan el hueco según `CB-03` y `RN-TU-04`) y sin romper `GET /api/mis-turnos?fecha=YYYY-MM-DD`.

2. **Indicadores visuales (dots) de turnos en el calendario mensual del odontólogo**:
   - Nuevo método `getMisTurnosCalendario(anio, mes)` en `frontend/src/services/dentist.service.ts` con tipado TypeScript estricto (Regla Dura #4).
   - Nuevo hook `useDentistCalendarQuery(anio, mes)` en `frontend/src/hooks/useDentistAgenda.ts` usando TanStack Query (Regla Dura #6), sincronizado e invalidado junto a `useUpdateAsistenciaMutation`.
   - En `OdontologoAgendaPage.tsx`, cada celda diaria muestra dots diferenciados por estado (confirmados en tono esmeralda y solicitados en ámbar, sin mostrar dot cuando no hay turnos), una leyenda compacta en el encabezado del calendario y atributos `aria-label`/`title` con el conteo del día.

3. **Script CLI separado e idempotente para poblar turnos demo adicionales (`seed_calendar_demo.py`)**:
   - Nuevo módulo `backend/app/infrastructure/seed_calendar_demo.py` y script ejecutable `backend/scripts/seed_calendar_demo.py` (`python -m scripts.seed_calendar_demo`).
   - Agrega un conjunto moderado y realista de turnos sintéticos (1 a 2 turnos en 3–4 días hábiles del mes actual, repartidos entre ambos odontólogos y ambos pacientes demo, mezclando estados `confirmado` y `solicitado`), alineados a los slots de 30 minutos de `PlantillaDisponibilidad`, validando no superposición de odontólogo ni sillón (`RN-AG-01`, `RN-AG-02`, Regla Dura #13) y garantizando idempotencia al re-ejecutarse.

## Capabilities

### New Capabilities
- *(Ninguna — se extiende la capacidad existente `odontologo-calendario`)*

### Modified Capabilities
- `odontologo-calendario`: Incorpora el resumen mensual de turnos del odontólogo (`GET /api/mis-turnos/calendario`), los indicadores visuales por día (dots) en `OdontologoAgendaPage.tsx` y el script complementario `seed_calendar_demo.py` para poblar turnos de demostración sin alterar `seed.py`.

## Impact

- **Backend**:
  - `backend/app/application/turnos.py` (helpers puros sincrónicos `get_clinic_month_bounds` y `summarize_dentist_month_appointments`).
  - `backend/app/api/mis_turnos.py` (schemas Pydantic con `extra="forbid"` y endpoint `GET /api/mis-turnos/calendario`).
  - `backend/app/infrastructure/seed_calendar_demo.py` y `backend/scripts/seed_calendar_demo.py`.
  - `backend/tests/test_mis_turnos.py` (o archivo dedicado `test_odontologo_calendario_endpoint.py`) y `backend/tests/test_seed_calendar_demo.py` contra PostgreSQL real (Regla Dura #7).
- **Frontend**:
  - `frontend/src/services/dentist.service.ts`
  - `frontend/src/hooks/useDentistAgenda.ts`
  - `frontend/src/pages/OdontologoAgendaPage.tsx`
  - `frontend/src/services/dentist.service.test.ts` y `frontend/src/pages/OdontologoAgendaPage.test.tsx`.
- **Base de datos y contratos**: No requiere nuevas migraciones Alembic ni modifica `GET /api/mis-turnos` ni `backend/scripts/seed.py`.
