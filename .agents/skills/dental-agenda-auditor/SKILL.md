---
name: dental-agenda-auditor
description: Audita especificaciones OpenSpec (proposal.md, design.md, specs/, tasks.md) y diseños de endpoints del dominio de agenda, plantillas de disponibilidad y turnos odontológicos contra las Reglas de Negocio (RN-AG, RN-TU, RN-GL) y las 13 Reglas Duras de turnos-odontologia. Usar SIEMPRE que se prepare, explore, proponga (/opsx:propose, /opsx:explore) o revise un change vinculado a plantillas horarias (PlantillaDisponibilidad), motor de disponibilidad (/api/disponibilidad), reserva o cancelación de turnos (/api/turnos) o vistas de agenda por rol (C-05 a C-10 y C-13 a C-15).
compatibility: Proyecto turnos-odontologia (FastAPI, SQLAlchemy 2.0, Pydantic v2, OpenSpec SDD).
---

# Dental Agenda & Turnos Auditor (`dental-agenda-auditor`)

Skill de dominio para auditar y verificar artefactos de **Spec-Driven Development (SDD)** sobre el motor de disponibilidad, plantillas semanales y gestión de turnos odontológicos antes de pasar a la etapa de implementación (`/opsx:apply`).

---

## 1. Propósito y Alcance

Evitar que pasen a implementación especificaciones con reglas de negocio ambiguas, huecos de validación horaria o contradicciones entre el alcance general de [`CHANGES.md`](../../../CHANGES.md), la Base de Conocimiento ([`knowledge-base/`](../../../knowledge-base/)) y las **13 Reglas Duras** de [`AGENTS.md`](../../../AGENTS.md).

---

## 2. Entradas Necesarias

Antes de ejecutar la auditoría, leer obligatoriamente:
1. **Artefactos del change bajo revisión** en `openspec/changes/<change-name>/`:
   - `proposal.md`
   - `design.md`
   - `specs/<capability>/spec.md`
   - `tasks.md`
2. **Fuentes de verdad del dominio**:
   - [`knowledge-base/04_modelo_de_datos.md`](../../../knowledge-base/04_modelo_de_datos.md) (`Usuario`, `PlantillaDisponibilidad`, `Turno`)
   - [`knowledge-base/05_reglas_de_negocio.md`](../../../knowledge-base/05_reglas_de_negocio.md) (`RN-AU-01..02`, `RN-TU-01..05`, `RN-AG-01..02`, `RN-GL-01..02`)
   - [`AGENTS.md`](../../../AGENTS.md) (11 Stack Rules + 2 Domain Rules)
3. **Modelos existentes en código** (cuando aplique):
   - [`backend/app/domain/models/plantilla.py`](../../../backend/app/domain/models/plantilla.py)
   - [`backend/app/domain/models/turno.py`](../../../backend/app/domain/models/turno.py)

---

## 3. Procedimiento de Auditoría (4 Pasos)

### Paso 1: Verificación de Reglas de Negocio (`RN-*`)
Contrastar cada requerimiento y escenario de `spec.md` contra las reglas aplicables del dominio:
- **`RN-AG-01` (Invariante anti-solape en servidor)**:
  - ¿Se valida en el servidor (transacción / constraint) que un mismo odontólogo no tenga dos plantillas ni dos turnos activos cuyos intervalos `[inicio, fin)` se superpongan (`inicio_A < fin_B AND fin_A > inicio_B`)?
- **`RN-AG-02` (Derivación estricta desde plantilla)**:
  - ¿Los huecos libres se calculan en tiempo real a partir de `PlantillaDisponibilidad` (`dia_semana`, `hora_inicio`, `hora_fin`, `duracion_slot_minutos`) menos los turnos que ocupan agenda, sin pre-generar turnos vacíos en la base de datos?
- **`RN-GL-01` y `RN-AU-02` (RBAC estricto en servidor)**:
  - ¿Las operaciones de escritura sobre plantillas están restringidas exclusivamente al rol `recepcion` (`403 Forbidden` para `paciente` y `odontologo`)?
  - ¿Las consultas de disponibilidad exigen usuario autenticado con contraseña actualizada (`require_password_changed` / `require_roles`)?
- **`RN-GL-02` (Prohibición de horarios pasados)**:
  - ¿Se rechazan o filtran consultas y reservas sobre fechas pasadas o bloques horarios ya transcurridos en la fecha actual según `TIMEZONE=America/Argentina/Buenos_Aires`?

### Paso 2: Matriz de Casos de Borde Horarios (Edge Cases Odontológicos)
Comprobar que `spec.md` y `design.md` definan comportamiento determinístico para los siguientes 6 casos de borde:

| ID | Caso de borde | Comportamiento exigido |
|---|---|---|
| **CB-01** | **Adyacencia exacta de intervalos (`fin_A == inicio_B`)** | Dos plantillas o turnos contiguos (ej. `09:00–11:00` y `11:00–13:00`) son **válidos** porque los intervalos son semiabiertos `[inicio, fin)`. No debe disparar falso positivo de solapamiento. |
| **CB-02** | **Ventana no divisible exactamente por `duracion_slot_minutos`** | Si `hora_fin - hora_inicio` no es múltiplo exacto de `duracion_slot_minutos` (ej. `09:00–10:00` con slots de `40 min`), solo se generan slots completos que terminen `<= hora_fin` (`slot_inicio + duracion <= hora_fin`), o bien se exige divisibilidad exacta al crear la plantilla. |
| **CB-03** | **Estados de turno que ocupan vs. liberan hueco (`RN-TU-04`)** | Turnos en `solicitado`, `confirmado`, `presente` o `ausente` **bloquean** el slot; turnos en `cancelado` (paciente) o `anulado` (recepción) **liberan** el slot para nuevas reservas. |
| **CB-04** | **Turno existente que solapa parcialmente un slot de plantilla** | Todo slot `[slot_inicio, slot_fin)` que cumpla `turno.inicio < slot_fin AND turno.fin > slot_inicio` con un turno no cancelado/anulado debe excluirse de la lista de huecos libres. |
| **CB-05** | **Consulta de disponibilidad en el día de hoy (`fecha == hoy`)** | En la fecha actual del consultorio (`TIMEZONE`), los slots cuyo `inicio <= ahora` deben omitirse aunque pertenezcan a una plantilla vigente (`RN-GL-02`). |
| **CB-06** | **Odontólogo inexistente o usuario cuyo rol no es `odontologo`** | Si `odontologo_id` no existe o pertenece a un `paciente`/`recepcion`, rechazar con `404 Not Found` o `422 Unprocessable Entity` al crear plantilla o consultar disponibilidad. |

### Paso 3: Control de las 13 Reglas Duras (`AGENTS.md`)
Revisar `design.md`, `spec.md` y `tasks.md` contra las restricciones técnicas innegociables:
1. **Regla Dura #1**: Todo schema Pydantic de entrada (`Create`, `Update`, `Filter`) declara `model_config = ConfigDict(extra="forbid")`.
2. **Regla Dura #2**: Los repositorios usan exclusivamente `select()` de SQLAlchemy 2.0 (prohibido `Session.query()`).
3. **Regla Dura #3**: No usar `async def` en funciones puras de cálculo en memoria (como la partición aritmética de slots de una plantilla) que no realicen I/O asíncrono real.
4. **Regla Dura #7**: Prohibido planificar mocks de base de datos (`unittest.mock`, `AsyncMock` sobre repositorios) en `tasks.md`; los tests deben ejercitar una base de datos real/transaccional.
5. **Regla Dura #8**: URIs basadas en sustantivos plurales (`/api/plantillas`, `/api/disponibilidad`), sin verbos en la ruta.
6. **Regla Dura #9**: **CRÍTICO**: Si `CHANGES.md` o un borrador menciona `PUT` para actualizar parcialmente un recurso (ej. `PUT /api/plantillas/{id}`), corregirlo a **`PATCH /api/plantillas/{id}`** y documentar la justificación.
7. **Regla Dura #12**: Todos los ejemplos, escenarios Gherkin (`WHEN`/`THEN`) y datos de prueba usan nombres y matrículas sintéticos ficticios (ej. `Dra. Sofía Martín (Ficticia)`, `paciente.ficticio@example.com`).
8. **Regla Dura #13**: Garantizar la no superposición horaria para el profesional asignado.

### Paso 4: Verificación de Escenarios Mínimos en `spec.md` y `tasks.md`
Confirmar que cada especificación contenga como mínimo:
- Al menos **1 escenario de funcionamiento esperado** (happy path).
- Al menos **1 escenario de error de negocio** (ej. solapamiento de plantillas, fecha pasada o rol no autorizado).
- Al menos **1 escenario de caso de borde** (ej. turno `cancelado`/`anulado` que libera hueco, adyacencia exacta `hora_fin == hora_inicio`, o remanente horario incompleto).
- En `tasks.md`, cada tarea de implementación debe indicar explícitamente **cómo se verificará cada escenario** mediante tests automatizados.

---

## 4. Formato del Resultado Esperado (Plantilla de Salida)

Al finalizar la auditoría, emitir el dictamen con esta estructura exacta:

```markdown
## Dictamen de Auditoría: `dental-agenda-auditor`
- **Change auditado**: `<nombre-del-change>`
- **Estado**: `APROBADO` | `CON OBSERVACIONES (requiere corrección)`

### 1. Checklist de Reglas de Negocio y Reglas Duras
| Criterio | Referencia | Estado | Evidencia / Ubicación |
|---|---|---|---|
| Invariante anti-solape en servidor | `RN-AG-01`, Regla #13 | ✅ / ❌ | ... |
| Derivación de huecos desde plantilla | `RN-AG-02` | ✅ / ❌ | ... |
| RBAC estricto y rechazo de fechas pasadas | `RN-GL-01`, `RN-GL-02` | ✅ / ❌ | ... |
| Schemas Pydantic con `extra="forbid"` | Regla Dura #1 | ✅ / ❌ | ... |
| Uso de `PATCH` en updates parciales (no `PUT`) | Regla Dura #9 | ✅ / ❌ | ... |
| Tests sin mocks de DB y con datos ficticios | Reglas Duras #7 y #12 | ✅ / ❌ | ... |

### 2. Cobertura de Casos de Borde (`CB-01` a `CB-06`)
- ...

### 3. Hallazgos y Correcciones Aplicadas (Antes vs. Después)
1. **[SEVERIDAD] Título del hallazgo**:
   - **Regla/Fuente**: ...
   - **Antes**: ...
   - **Después (Corrección)**: ...
```

---

## 5. Criterios para Revisar el Resultado de la Skill

El resultado producido por esta skill es válido únicamente si:
1. Cita los códigos exactos de reglas (`RN-AG-01`, `RN-AG-02`, `RN-GL-01`, `RN-GL-02`) y números de Reglas Duras (`#1` a `#13`).
2. Verifica que `spec.md` incluya escenarios de funcionamiento esperado, error de negocio y caso de borde verificables con `WHEN` / `THEN`.
3. Detecta y corrige cualquier discrepancia entre `CHANGES.md` y `AGENTS.md` (como el uso de `PUT` vs `PATCH` o funciones `async def` sin I/O).
