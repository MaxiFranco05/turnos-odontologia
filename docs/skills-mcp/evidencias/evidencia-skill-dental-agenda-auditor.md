# Evidencia de Uso de la Skill Propia: `dental-agenda-auditor`

**Fecha**: 2026-11-01
**Change auditado**: `c-05-availability-engine`
**Modalidad**: sesión nueva de agente (subagente de solo lectura sin contexto previo de la conversación), que debía encontrar la skill únicamente a partir de las instrucciones de la fundación.

---

## 1. Solicitud realizada (resumen fiel del prompt)

> Estás iniciando en una sesión nueva dentro del repositorio `turnos-odontologia`.
> 1. Leé `AGENTS.md` y `.atl/skill-registry.md` para identificar qué skill corresponde usar para auditar especificaciones de agenda, plantillas horarias y disponibilidad, y en qué ruta se encuentra.
> 2. Leé el `SKILL.md` de esa skill y seguí su procedimiento de 4 pasos.
> 3. Auditá los artefactos de `openspec/changes/c-05-availability-engine/` contra `knowledge-base/04_modelo_de_datos.md`, `knowledge-base/05_reglas_de_negocio.md` y `AGENTS.md`.
> 4. Evaluá críticamente si existe alguna omisión o caso de borde adicional (por ejemplo, un turno que solapa dos slots consecutivos, o un `PATCH` con payload vacío `{}`).
> 5. Devolvé el dictamen con la plantilla `## Dictamen de Auditoría: dental-agenda-auditor`.

> [!NOTE]
> El paso 4 sugería dos casos a revisar. Esta sugerencia la agregó quien redactó la solicitud y se tiene en cuenta en la revisión crítica de `aplicacion.md`: dos de los cuatro hallazgos vinieron guiados por la solicitud y dos los encontró el agente por su cuenta.

Primer intento: la sesión no llegó a ejecutarse por un error de cuota del proveedor (`RESOURCE_EXHAUSTED (code 429)`). Se repitió la misma solicitud con otro modelo y se completó.

## 2. Descubrimiento de la skill (resultado del agente)

- Skill identificada: `dental-agenda-auditor`, en `.agents/skills/dental-agenda-auditor/SKILL.md`.
- La encontró a partir de `AGENTS.md` (secciones *Skills Disponibles* y *Skill Propia del Dominio*) y de `.atl/skill-registry.md` (tabla *User Skills* y *Compact Rules*).

## 3. Resultado obtenido (extracto del dictamen)

- **Estado**: `CON OBSERVACIONES (requiere corrección)`.
- Checklist: `RN-AG-02`, Reglas Duras #1, #3, #7, #9 y #12 → ✅. `RN-AG-01` y `RN-GL-01/02` → ✅ con observaciones.
- Casos de borde: `CB-01`, `CB-02`, `CB-03`, `CB-05` → cubiertos. `CB-04` → **omitido**. `CB-06` → **incompleto**.

| # | Severidad | Hallazgo |
|---|---|---|
| 1 | ALTA | `spec.md` no tenía escenario para un turno que abarca o atraviesa varios slots (`CB-04`); el único escenario usaba un turno alineado a un solo slot. |
| 2 | MEDIA | No estaba definido qué responde `PATCH /api/plantillas/{id}` con payload vacío `{}`. |
| 3 | MEDIA | `CB-06` (odontólogo inexistente o rol no odontólogo) estaba cubierto para `POST /api/plantillas`, pero no para `GET /api/disponibilidad`. |
| 4 | BAJA | Faltaban escenarios de `PATCH` que genera solapamiento (`409`) y de `id` inexistente (`404`). |

## 4. Qué aportó al change

Las 4 observaciones se incorporaron a `specs/availability-engine/spec.md`, `tasks.md` (3.2 y 4.1) y `design.md` (Decisión 1). Luego `openspec validate c-05-availability-engine --strict` volvió a dar **válido**. El antes y después está en `docs/skills-mcp/aplicacion.md` §4.
