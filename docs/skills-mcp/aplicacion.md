# Informe de Aplicación: Skill Propia + MCP en el change `C-05`

**Proyecto**: `turnos-odontologia` · **Grupo**: LocalHost · **Fecha**: 2026-11-02

## 1. Resultados

| Entregable | Estado | Ubicación |
|---|---|---|
| Skill propia `dental-agenda-auditor` | Creada, registrada y usada en una sesión nueva | [`.agents/skills/dental-agenda-auditor/SKILL.md`](../../.agents/skills/dental-agenda-auditor/SKILL.md) |
| Servidor MCP `playwright` | Conectado y probado; se ejecutó `browser_navigate` e inspección de snapshot DOM | [`mcp_config.example.json`](../../mcp_config.example.json), [`README.md`](../../README.md) |
| Change `c-05-availability-engine` | **Preparado** (4/4 artefactos, `openspec validate --strict` válido). **No implementado ni archivado.** | [`openspec/changes/c-05-availability-engine/`](../../openspec/changes/c-05-availability-engine/) |

La especificación tiene 6 requisitos y 20 escenarios. Incluye escenarios de funcionamiento esperado (alta de plantilla, cálculo de huecos), de error de negocio (solapamiento `409`, rol no autorizado `403`, fecha pasada `422`) y de borde (`CB-01` a `CB-06`, `PATCH {}`). Cada tarea de `tasks.md` indica el test que verificará cada escenario.

**Evidencias**: [evidencia-skill-dental-agenda-auditor.md](evidencias/evidencia-skill-dental-agenda-auditor.md) · [evidencia-mcp-playwright.md](evidencias/evidencia-mcp-playwright.md)

## 2. Uso de las incorporaciones en la preparación del change

- **MCP `playwright`**: la navegación automatizada con `browser_navigate` e inspección del árbol semántico en la documentación oficial viva de FastAPI (`https://fastapi.tiangolo.com/tutorial/body-updates/`) confirmó los patrones canónicos para actualizaciones parciales mediante `PATCH` y `model_dump(exclude_unset=True)`. Esto fundamentó la Decisión 1 de `design.md` y permitió identificar que validar `hora_fin > hora_inicio` únicamente sobre el payload parcial es insuficiente: debe validarse el estado ya fusionado con la entidad guardada.
- **Skill `dental-agenda-auditor`**: auditó los 4 artefactos en una sesión nueva de subagente descubierta a través de `AGENTS.md` y `.atl/skill-registry.md`, encontrando 4 omisiones que se incorporaron formalmente a la especificación (ver §4).

## 3. Archivos modificados y motivo

| Archivo | Motivo |
|---|---|
| `.agents/skills/dental-agenda-auditor/SKILL.md` (nuevo) | Skill propia versionada en el repo (Paso 5). |
| `.atl/skill-registry.md` | Registro de la skill: nombre, propósito, ubicación y Compact Rules. |
| `AGENTS.md` / `CLAUDE.md` | Cuándo usar la skill y qué necesita; sección *Integraciones MCP* con Playwright (`@playwright/mcp`); flujo actualizado. Los dos archivos quedaron idénticos. |
| `knowledge-base/09_decisiones_y_supuestos.md` | Decisión arquitectónica `DD-08` que justifica ambas incorporaciones. |
| `mcp_config.example.json` (nuevo) | Configuración de ejemplo sin secretos para Playwright MCP (`--browser msedge`). |
| `README.md` | Requisitos, configuración, comprobación y troubleshooting de Playwright MCP; reproducción de la skill. |
| `openspec/changes/c-05-availability-engine/*` (nuevo) | Artefactos SDD del change preparados y validados (Paso 7). |
| `CHANGES.md` | C-05 queda como "preparado — listo para implementar" (sigue `[ ]`); corrección de `PUT` a `PATCH`. |
| `docs/skills-mcp/*` | Ficha de investigación, informe de aplicación, evidencias y plantilla de entrega. |

## 4. Revisión crítica (antes y después)

**Hallazgo A — Contradicción en el roadmap (detectada al preparar el change).** Se encontró al cruzar el alcance de `CHANGES.md` con las Reglas Duras de `AGENTS.md`. La regla que permitió corregirlo es la **Regla Dura #9**.
- *Antes*: `CHANGES.md` C-05 indicaba `POST/GET/PUT/DELETE /api/plantillas`.
- *Después*: Se corrigió a `POST/GET/PATCH/DELETE`, fundamentado con la inspección en FastAPI vía Playwright MCP (`design.md` Decisión 1).

**Hallazgo B — Omisión en la spec que generamos con el agente (detectada por la skill).** La salida inicial del agente cubría `CB-04` solo en el algoritmo de `design.md`. En `spec.md`, el único escenario usaba un turno alineado a un slot (`09:30–10:00`). La skill lo detectó con su matriz de casos de borde (`CB-04`, `RN-AG-01`).
- *Antes*: No había escenario ni test para un turno desfasado o que cubra más de un slot.
- *Después*: Nuevo escenario en `spec.md`: un turno de `09:15–10:15` sobre slots de 30 minutos bloquea `09:00–09:30`, `09:30–10:00` y `10:00–10:30`; solo queda libre `10:30–11:00`. Test agregado en `tasks.md` §4.1.

Se aplicaron también: `PATCH {}` → `200` sin cambios (RFC 7396; decisión técnica, no de dominio), `CB-06` en `/api/disponibilidad`, `PATCH` que genera solapamiento → `409` y `id` inexistente → `404`.

**Problemas técnicos reales resueltos durante la integración:**
1. **Detección de Chrome en Playwright MCP (Windows):** Al ejecutar `@playwright/mcp@latest`, el proceso fallaba con `Chromium distribution 'chrome' is not found at AppData\Local\Google\Chrome\Application\chrome.exe`. Se solucionó configurando `--browser msedge`, que aprovecha Microsoft Edge nativo en Windows de forma limpia y reproducible.
2. **Cuota del agente en sesión nueva:** El primer intento de lanzar un subagente para probar la skill falló con `429 RESOURCE_EXHAUSTED` y debió relanzarse con modelo `flash`.
3. **Pendientes de verificación:** La ficha explicita transparentemente que el comando `npx skills add anthropics/skills --skill skill-creator` no se ejecutó porque la skill ya estaba en el entorno.

## 5. Limitaciones

- **Uso de `skill-creator`**: La skill propia se redactó siguiendo la guía de `skill-creator` (estructura, *frontmatter* y descripción con disparadores explícitos). No se corrió su ciclo de evaluaciones automáticas (`evals`/benchmark).
- **Sesgo en la prueba de la skill**: La solicitud a la sesión nueva sugería dos casos (`CB-04`, `PATCH {}`). Por eso solo los hallazgos 3 y 4 cuentan como detección completamente autónoma de la skill.
- **Alcance de Playwright MCP**: Es una herramienta de automatización e inspección web; no realiza consultas directas sobre PostgreSQL (las pruebas sobre DB real se delegan a la suite de tests en `apply`).
- **Regla Dura #13 (sillón/box)**: El modelo de datos v1 no tiene entidad sillón/box; C-05 garantiza la no superposición por profesional odontólogo.
- Los escenarios aún no se ejecutaron como código de producción: corresponden a `/opsx:apply`, en una instancia posterior del proyecto.
