# Ficha de Investigación: Integración de Skill Propia y Servidor MCP

**Proyecto**: `turnos-odontologia` (Sistema de Gestión de Turnos Odontológicos)  
**Materia**: Metodología de Sistemas I — Tecnicatura Universitaria en Programación (UTN)  
**Fecha**: 2026-11-02  

---

## 1. Necesidad Detectada y Change Elegido

### Estado actual del repositorio y selección del Change
Tras revisar [`CHANGES.md`](../../CHANGES.md) y el historial del repositorio, los changes `C-01` (`foundation-setup`), `C-02` (`core-models`), `C-03` (`auth-jwt`), `C-04` (`password-reset-flow`) y `C-11` (`frontend-scaffold`) ya se encuentran implementados, verificados y archivados en `openspec/changes/archive/`.

Se selecciona el change pendiente **`[C-05] availability-engine`** (Motor de disponibilidad y plantillas horarias), cuya única dependencia obligatoria en [`CHANGES.md`](../../CHANGES.md) es `C-02` (ya completado, junto con `C-03` para los guards RBAC `require_roles`). Su alcance comprende:
1. CRUD de `PlantillaDisponibilidad` exclusivo para el rol `recepcion` (`/api/plantillas`) con validación de no superposición de plantillas para un mismo odontólogo y día de la semana (`dia_semana` 0–6).
2. Endpoint `GET /api/disponibilidad?odontologo_id=&fecha=` que deriva dinámicamente los huecos libres restando a los bloques de la plantilla los turnos activos (`solicitado`, `confirmado`, `presente`, `ausente`) y liberando los turnos con estado `cancelado` o `anulado`.

### Problemas detectados que motivan las incorporaciones
1. **Tarea repetible para una Skill propia (Auditoría de reglas de agenda y casos de borde)**:
   Al preparar especificaciones SDD para `C-05` (y futuros changes como `C-06` y `C-07`), el agente debe cruzar manualmente las reglas de [`knowledge-base/05_reglas_de_negocio.md`](../../knowledge-base/05_reglas_de_negocio.md) (`RN-AG-01`, `RN-AG-02`, `RN-GL-01`, `RN-GL-02`) con las **13 Reglas Duras** de [`AGENTS.md`](../../AGENTS.md). Durante el análisis preliminar ya se detectó una contradicción real: el alcance descriptivo de `C-05` en `CHANGES.md` sugiere `PUT /api/plantillas`, mientras que la **Regla Dura #9** prohíbe `PUT` para actualizaciones parciales y exige `PATCH`. Además, en el cálculo de slots suelen omitirse casos de borde críticos (ventanas horarias no divisibles exactamente por `duracion_slot_minutos`, plantillas contiguas donde `hora_fin == hora_inicio`, horarios pasados dentro del día actual según `TIMEZONE=America/Argentina/Buenos_Aires` y exclusión de estados `cancelado`/`anulado`).
2. **Necesidad de información externa y herramientas para un Servidor MCP (Inspección y navegación web automatizada)**:
   Para diseñar rigurosamente los artefactos técnicos (`design.md`, `specs/`) de `C-05` sin recurrir a suposiciones, el agente necesita inspeccionar documentación técnica viva y contratos de endpoints en la web (como la documentación oficial de FastAPI sobre actualizaciones parciales mediante `PATCH` y `model_dump(exclude_unset=True)`). Un servidor MCP de automatización de navegador permite navegar a especificaciones y documentación web, extraer snapshots estructurados de accesibilidad (árbol DOM semántico) y verificar patrones oficiales de forma determinística.

### Sinergia en la preparación de `C-05`
- El **servidor MCP (`playwright`)** permite al agente navegar e inspeccionar en vivo las guías oficiales de FastAPI y RFCs relevantes en la web, capturando snapshots del DOM para validar contratos REST (`PATCH`, `exclude_unset`) y estructuras de datos.
- La **skill propia (`dental-agenda-auditor`)** evalúa `proposal.md`, `design.md`, `specs/` y `tasks.md` contra las reglas de negocio odontológicas, la matriz de casos de borde de intervalos horarios y las 13 Reglas Duras antes de dar por listo el change.

---

## 2. Investigación de Skill Creadora y Diseño de la Skill Propia

### Skill creadora seleccionada
| Atributo | Detalle |
|---|---|
| **Nombre** | `skill-creator` |
| **Fuente oficial / Autor** | Anthropic — Repositorio oficial [`anthropics/skills`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) y catálogo [`skills.sh`](https://skills.sh/) |
| **Compatibilidad** | Compatible con Antigravity (`.agents/skills/`, `~/.gemini/config/skills/`), Claude Code (`.claude/skills/`) y OpenCode (`~/.config/opencode/skills/`). Registrada en [`.atl/skill-registry.md`](../../.atl/skill-registry.md). |
| **Instalación y verificación** | Ya instalada en el equipo en `~/.gemini/config/skills/skill-creator/SKILL.md` (verificado). Comando de instalación sugerido `npx skills add anthropics/skills --skill skill-creator` — **pendiente de verificar**. Se comprueba por la existencia de `SKILL.md` en la carpeta de skills del agente. |

### Diseño de la skill propia: `dental-agenda-auditor`
- **Propósito**: Auditar artefactos OpenSpec (`proposal.md`, `design.md`, `specs/`, `tasks.md`) y contratos de API del dominio de agenda y turnos odontológicos para detectar ambigüedades, casos de borde horarios faltantes y violaciones a la Base de Conocimiento o a las 13 Reglas Duras.
- **Cuándo se activa (Trigger)**: Al preparar, explorar o revisar un change de agenda/turnos (`/opsx:explore`, `/opsx:propose` en `C-05`, `C-06`, `C-07`, `C-08`, `C-09`, `C-10`) o cuando el usuario pida revisar escenarios de disponibilidad, plantillas horarias o solapamientos.
- **Entradas necesarias**: Artefactos del change en `openspec/changes/<change>/`, [`knowledge-base/04_modelo_de_datos.md`](../../knowledge-base/04_modelo_de_datos.md), [`knowledge-base/05_reglas_de_negocio.md`](../../knowledge-base/05_reglas_de_negocio.md), [`AGENTS.md`](../../AGENTS.md) y [`CHANGES.md`](../../CHANGES.md).
- **Procedimiento paso a paso**:
  1. **Control de Reglas de Dominio**: Verificar trazabilidad explícita hacia `RN-AG-01` (anti-solape en servidor), `RN-AG-02` (derivación de huecos desde `PlantillaDisponibilidad`), `RN-GL-01` (RBAC por rol) y `RN-GL-02` (rechazo de fechas/horas pasadas).
  2. **Matriz de Casos de Borde Horarios**: Comprobar cobertura de: (a) solapamiento parcial `[inicio, fin)` vs. adyacencia válida `fin == inicio`; (b) división entera de `(hora_fin - hora_inicio)` por `duracion_slot_minutos` descartando remanentes incompletos; (c) estados que ocupan hueco (`solicitado`, `confirmado`, `presente`, `ausente`) vs. estados que liberan hueco (`cancelado`, `anulado`); (d) filtro de slots pasados en la fecha actual según `TIMEZONE`.
  3. **Auditoría de Reglas Duras**: Verificar `extra="forbid"` en schemas Pydantic (Regla #1), `select()` 2.0 (Regla #2), URIs sustantivas (Regla #8), uso de `PATCH` en lugar de `PUT` para updates parciales (Regla #9), tests contra DB real sin mocks (Regla #7) y datos sintéticos ficticios (Regla #12).
  4. **Emisión de Dictamen**: Generar tabla de verificación y listado de hallazgos (`BLOQUEANTE`, `ADVERTENCIA`, `SUGERENCIA`) con corrección propuesta.
- **Resultado esperado y criterios de revisión**: Reporte estructurado en Markdown que acredite al menos 3 escenarios verificables (esperado, error de negocio y borde), trazabilidad a códigos `RN-*` y ausencia de datos reales o mocks de base de datos.
- **Ubicación y referencia**: Se guardará versionada en `.agents/skills/dental-agenda-auditor/SKILL.md` y se registrará en `.atl/skill-registry.md`, `AGENTS.md` y `CLAUDE.md`.

---

## 3. Investigación y Selección del Servidor MCP

### Comparación de dos servidores MCP existentes

| Criterio | Opción A: Playwright MCP (`@playwright/mcp`) | Opción B: PostgreSQL MCP (`@modelcontextprotocol/server-postgres`) |
|---|---|---|
| **Propósito** | Navegación e interacción web automatizada; genera snapshots semánticos del DOM/árbol de accesibilidad para inspección de documentación técnica, consolas de API y flujos web. | Conectar el agente a una base de datos PostgreSQL para inspeccionar esquemas y ejecutar consultas SQL de solo lectura (`SELECT`). |
| **Capacidades (Tools)** | `browser_navigate` (navega a URLs), `browser_snapshot` (extrae árbol semántico de la página), `browser_click`, `browser_fill_form`, `browser_evaluate`, `browser_console_messages`. | `query` (ejecuta consultas SQL en transacción READ ONLY), recursos `postgres://<host>/<table>/schema`. |
| **Compatibilidad con el agente** | Compatible con clientes MCP (Antigravity, Claude Code, Cursor) vía `stdio` (`npx`). | Compatible con clientes MCP vía `stdio` (`npx`), pero el paquete se encuentra formalmente deprecado en npm (`deprecated @modelcontextprotocol/server-postgres@0.6.2`). |
| **Requisitos de instalación / conexión** | Node.js >= 18 + `npx -y @playwright/mcp@latest --browser msedge` (o chrome). No requiere levantar servicios locales ni contenedores. | Node.js >= 18 + instancia PostgreSQL activa y accesible en red local (`5432`) o Docker Desktop en ejecución. |
| **Permisos y credenciales** | Sin secretos ni contraseñas requeridas en la configuración; navegación controlada por host (`--allowed-hosts`). | Requiere inyectar credenciales sensibles de base de datos (`POSTGRES_USER`, `POSTGRES_PASSWORD`) en la configuración del cliente. |
| **Costos** | Gratuito y de código abierto (Apache 2.0, Microsoft). | Gratuito y de código abierto (MIT). |

### Justificación de la elección: **Playwright MCP (`playwright`)**
Se selecciona **Playwright MCP** por tres razones fundamentales:
1. **Reproducibilidad garantizada sin dependencias de infraestructura**: No requiere que el servicio de PostgreSQL de cada integrante tenga credenciales idénticas ni que Docker Desktop esté encendido. Funciona de manera inmediata sobre cualquier entorno con Node.js y un navegador preinstalado (Edge en Windows o Chromium en Linux/macOS).
2. **Soporte activo vs. paquete deprecado**: El paquete oficial `@playwright/mcp` es mantenido activamente por Microsoft Playwright, mientras que `@modelcontextprotocol/server-postgres` fue archivado/deprecado en npm.
3. **Aporte concreto a la preparación técnica de `C-05`**: Permite al agente navegar directamente a documentación técnica oficial viva (como la documentación de FastAPI sobre `PATCH` y Pydantic `exclude_unset`), extrayendo el árbol de accesibilidad y el código normativo para contrastar el diseño de `design.md` contra fuentes primarias.

### Configuración, comprobación y límites de seguridad
- **Configuración reproducible (`mcp_config.example.json`)**:
  ```json
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest", "--browser", "msedge"]
      }
    }
  }
  ```
- **Comprobación y ejecución**: Inicializar el servidor y ejecutar `browser_navigate` hacia una URL de documentación técnica (ej. `https://fastapi.tiangolo.com/tutorial/body-updates/`), verificando la respuesta y el snapshot semántico generado.
- **Información consultada y límites con datos de prueba**:
  - **Acceso**: Exclusivamente lectura de documentación técnica pública externa y endpoints locales de desarrollo; no modifica archivos locales de código.
  - **Límites de Privacidad (Regla Dura #12)**: Prohibido ingresar o transmitir datos reales de pacientes (nombres, DNI, teléfonos) en formularios web o parámetros de URL; operar únicamente con datos sintéticos y URLs de documentación técnica.

---

## 4. Archivos de la Fundación que se Prevén Actualizar

1. `.agents/skills/dental-agenda-auditor/SKILL.md`: Creación de la skill propia versionada en el repositorio.
2. [`.atl/skill-registry.md`](../../.atl/skill-registry.md): Registro de `dental-agenda-auditor` en la tabla `User Skills` y adición de sus reglas compactas en `Compact Rules`.
3. [`AGENTS.md`](../../AGENTS.md) y [`CLAUDE.md`](../../CLAUDE.md): Actualización sincronizada de la tabla `Skills Disponibles` y nueva sección de **Integraciones MCP** (propósito, herramientas, cuándo usarlo y límites de seguridad de `playwright`).
4. [`README.md`](../../README.md): Documentación reproducible de requisitos, configuración sin secretos, verificación y troubleshooting del servidor MCP `playwright` y de la skill propia.
5. [`knowledge-base/09_decisiones_y_supuestos.md`](../../knowledge-base/09_decisiones_y_supuestos.md): Decisión `DD-08` que fundamenta arquitectónicamente ambas incorporaciones.
6. [`CHANGES.md`](../../CHANGES.md) y `openspec/changes/c-05-availability-engine/`: Artefactos SDD preparados (`proposal.md`, `design.md`, `specs/availability-engine/spec.md`, `tasks.md`) y referencia de estado en el roadmap.

---

## 5. Fuentes Consultadas

1. **Anthropic Skills Repository (`skill-creator`)** — Documentación oficial y código fuente de `skill-creator`: https://github.com/anthropics/skills/tree/main/skills/skill-creator (Consultado: 2026-11-01).
2. **Model Context Protocol (MCP) — Especificación y Documentación Oficial**: https://modelcontextprotocol.io/introduction (Consultado: 2026-11-01).
3. **Microsoft Playwright MCP Server (`@playwright/mcp`)** — Repositorio oficial y capacidades de automatización del navegador: https://github.com/microsoft/playwright-mcp (Consultado: 2026-11-02).
4. **MCP Reference Servers (`@modelcontextprotocol/server-postgres`)** — Repositorio archivado de servidores de referencia: https://github.com/modelcontextprotocol/servers (Consultado: 2026-11-01).
5. **FastAPI Official Documentation (Body - Updates)** — Guía oficial sobre actualizaciones con `PATCH` y `exclude_unset=True`: https://fastapi.tiangolo.com/tutorial/body-updates/ (Consultado vía Playwright MCP: 2026-11-02).

### Pendientes de verificación
- El comando de instalación `npx skills add anthropics/skills --skill skill-creator` y el catálogo `skills.sh` no se ejecutaron ni contrastaron: en el equipo la skill ya estaba instalada en `~/.gemini/config/skills/skill-creator/`.
- La fuente 4 (`server-postgres`) se constató deprecada en npm al ejecutar pruebas locales. Las fuentes 1 y 2 deben ser abiertas por el equipo para confirmar la fecha de consulta; la fuente 5 sí se navegó e inspeccionó directamente con Playwright MCP (ver `evidencias/evidencia-mcp-playwright.md`).
