# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — v1 sin integraciones externas obligatorias

**Decisión**: la v1 no integra WhatsApp, pagos, PUCO ni ARCA.
**Contexto**: alcance académico acotado; cada integración es costo y riesgo.
**Alternativas consideradas**: incluir recordatorios por WhatsApp desde v1.
**Justificación**: el Discovery lo fija como restricción y el análisis
competitivo muestra que casi ningún competidor AR lo incluye gratis.
**Trade-offs aceptados**: sin recordatorios ni cobros en el lanzamiento;
canal de recordatorios definido: email primero, WhatsApp después.

### DD-02 — Login con correo o N.º de socio + contraseña

**Decisión**: ambos identificadores válidos para el paciente.
**Contexto**: consultorios con pacientes de obra social (N.º afiliado) y
particulares (correo).
**Alternativas consideradas**: solo correo; login social.
**Justificación**: decidido con el usuario en Discovery; cubre ambos
perfiles sin dependencias externas.
**Trade-offs aceptados**: flujo de registro de cuentas pendiente de diseño
(ver pregunta Alta-3).

### DD-03 — Máquina de estados mínima por rol estricta

**Decisión**: `solicitado → confirmado / anulado` (recepción),
`cancelado` (paciente), `presente / ausente` (odontólogo).
**Contexto**: los 18 competidores relevados usan catálogos extensos y
difusos.
**Alternativas consideradas**: adoptar un catálogo amplio «como el mercado».
**Justificación**: la simplicidad es posicionamiento y reduce errores de
implementación.
**Trade-offs aceptados**: si el consultorio pide más estados, se amplía en
v2 (pregunta Alta-5).

### DD-04 — Anti-solapamiento como invariante de servidor

**Decisión**: constraint + validación transaccional, nunca solo cliente.
**Contexto**: es la regla que elimina las dobles reservas manuales.
**Alternativas consideradas**: validación solo en UI.
**Justificación**: ningún competidor la publica verificable; es el
diferencial día 1.
**Trade-offs aceptados**: reintentos visibles si dos pacientes compiten por
el mismo hueco (flujo 2 lo maneja).

### DD-05 — Escalera de etapas v2/v3

**Decisión**: post-MVP recordatorios + reprogramación + lista de espera;
v2 señas con Mercado Pago; v3 obras sociales + PUCO + ARCA.
**Contexto**: orden de complejidad real evidenciada en el mercado.
**Alternativas consideradas**: incluir cobros en v1.
**Justificación**: cada etapa agrega una sola familia de riesgo.
**Trade-offs aceptados**: v1 sin ingresos ni obra social dentro del sistema.

### DD-06 — Stack de cátedra (FastAPI + React + PostgreSQL, JWT, Redis futuro)

**Decisión**: backend Python + FastAPI + SQLAlchemy, auth JWT, PostgreSQL,
frontend React + TypeScript + Vite, Docker/Compose; Redis previsto para
versiones posteriores, sin uso en v1.
**Contexto**: stack sugerido por el profesor y la cátedra.
**Alternativas consideradas**: ninguna (lineamiento de cátedra).
**Justificación**: cubre los invariantes del proyecto (transaccionalidad
Postgres para RN-AG-01, claims JWT para RBAC) con tecnología estándar.
**Trade-offs aceptados**: Redis como infra dormida hasta v2; expiración JWT
y esquema de refresh pendientes de detalle.

### DD-07 — Alta de cuentas por recepción + contraseña temporal

**Decisión**: recepción crea la cuenta con datos esenciales y contraseña
temporal; el primer login obliga a cambiarla y completar datos; los
sensibles los carga el paciente.
**Contexto**: sin auto-registro público en v1.
**Alternativas consideradas**: auto-registro público con validación.
**Justificación**: evita spam y cuentas falsas con costo mínimo (carga
inicial por recepción); el flag `debe_cambiar_password` garantiza que la
temporal no quede vigente.
**Trade-offs aceptados**: recepción absorbe el alta; la escalabilidad del
alta se revisa si el volumen crece.

### DD-08 — Incorporación de skill propia (`dental-agenda-auditor`) e integración MCP (`playwright`)

**Decisión**: incorporar a la fundación del proyecto la skill propia de
dominio `dental-agenda-auditor` (`.agents/skills/dental-agenda-auditor/SKILL.md`)
y el servidor MCP `playwright` (`@playwright/mcp`).
**Contexto**: necesidad de evitar omisiones de casos de borde horarios y
contradicciones con las 13 Reglas Duras al especificar changes de agenda/turnos
(`C-05` a `C-10`), y de inspeccionar documentación técnica oficial viva y
árboles semánticos de accesibilidad durante `/opsx:propose`.
**Alternativas consideradas**: revisión manual ad-hoc de specs y servidor MCP
`@modelcontextprotocol/server-postgres` conectado a la base local.
**Justificación**: `dental-agenda-auditor` estandariza un checklist verificable
de reglas `RN-AG`/`RN-TU` y casos de borde horarios (`CB-01` a `CB-06`), mientras
que `playwright` provee automatización de navegador de solo lectura, inspección de
árboles de accesibilidad DOM y validación de contratos sin requerir credenciales
de base de datos ni servicios locales activos, garantizando máxima reproducibilidad
entre los integrantes.
**Trade-offs aceptados**: `playwright` navega e inspecciona páginas web de
documentación o interfaces locales (no ejecuta consultas SQL directas en la DB) y
requiere un navegador preinstalado (Edge o Chromium).

## Supuestos inferidos

### SU-01 — Disponibilidad por plantilla

**Supuesto**: los huecos se derivan de una plantilla por odontólogo en vez
de cargarse turno por turno.
**Origen**: recomendación D.3 del informe (`docs/discovery/`), no del
checklist Q&A.
**Riesgo si es falso**: si el consultorio quiere carga manual, RN-AG-02 y el
modelo de `PlantillaDisponibilidad` cambian.
**Cómo validar**: confirmar con el consultorio antes del Sprint 1.

### SU-02 — Sistema web multi-rol

**Supuesto**: `system_type = web_app` (reserva online + login implican app
web).
**Origen**: inferido del informe; sin confirmación explícita.
**Riesgo si es falso**: cambia stack, entrega y UX por completo.
**Cómo validar**: pregunta Alta-1 de `10_preguntas_abiertas.md`.

### SU-03 — Consultorio único (single-tenant)

**Supuesto**: una instalación = un consultorio; sin multi-sede ni
multi-tenant en v1.
**Origen**: inferido del alcance académico; el informe excluye multi-sede
de v1.
**Riesgo si es falso**: el modelo de datos y RBAC se complican.
**Cómo validar**: pregunta Media-1.
