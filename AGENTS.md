# turnos-odontologia — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

<!-- Copiar la tabla de knowledge-base/02_descripcion_general.md §Stack tecnológico -->

| Capa | Tecnología | Estado |
|------|------------|--------|
| Frontend | React + TypeScript + Vite | Definido por cátedra |
| Backend | Python + FastAPI + SQLAlchemy (ORM) | Definido por cátedra |
| Base de datos | PostgreSQL | Definida por cátedra |
| Auth | JWT con credenciales propias (correo o N.º socio + contraseña) | Definido; esquema de sesión en `08` |
| Async (futuro) | Redis (recordatorios y tareas desde v2) | Previsto, no se usa en v1 |
| Entornos | Docker / Docker Compose (api + postgres + redis) | Definido por cátedra |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura, env vars |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones arquitectónicas (`DD-01` a `DD-08`) y supuestos |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |

> ⚠️ Resolver las preguntas de prioridad **Alta** de `10_preguntas_abiertas.md` antes de arrancar el primer change.

---

## Skills Disponibles

<!-- Fuente de verdad: .atl/skill-registry.md (generado por skill-registry). Adaptar filas a las skills que lista el registry; fallback a .claude/skills/ y ~/.claude/skills/ si no existe. -->

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI / SQLAlchemy / UoW / migraciones | `fastapi`, `python-sqlalchemy`, `tdd`, `loom-data-validation`, `mastering-postgresql`, `dental-agenda-auditor` |
| **Backend Aux** | Servicios, integraciones, disponibilidad, agendas | `rest-api-guidelines`, `jwt-auth`, `docker-init`, `openspec-archive-change`, `dental-agenda-auditor` |
| **Frontend** | React / TypeScript / Vite / TanStack Query / Tailwind | `fe-react-dev-stack`, `fe-fullstack-dev`, `javascript-testing-patterns`, `design-taste-frontend`, `emil-design-eng`, `ui-ux-pro-max`, `vercel-react-best-practices` |
| **Orquestación** | SDD / OPSX / docs / KB / Roadmap | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agents-md-generator`, `skill-registry`, `find-skill`, `skill-creator`, `dental-agenda-auditor` |

Cargá la skill correspondiente al contexto ANTES de escribir código o especificaciones.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md`. Esta tabla mapea skill→rol.

### Skill Propia del Dominio: `dental-agenda-auditor`

- **Ubicación**: [`.agents/skills/dental-agenda-auditor/SKILL.md`](.agents/skills/dental-agenda-auditor/SKILL.md)
- **Propósito**: Auditar artefactos SDD (`proposal.md`, `design.md`, `specs/`, `tasks.md`) y contratos de endpoints del dominio de agenda, plantillas horarias (`PlantillaDisponibilidad`) y turnos (`Turno`).
- **Cuándo usarla**:
  - Durante `/opsx:explore` y `/opsx:propose` al preparar o revisar changes vinculados a disponibilidad, plantillas o turnos (`C-05`, `C-06`, `C-07`, `C-08`, `C-09`, `C-10`, `C-13`, `C-14`, `C-15`).
  - Antes de aprobar un change para `/opsx:apply`, para detectar contradicciones entre `CHANGES.md`, la Base de Conocimiento y las 13 Reglas Duras.
- **Qué entradas necesita**:
  1. Artefactos del change bajo análisis en `openspec/changes/<change>/`.
  2. [`knowledge-base/04_modelo_de_datos.md`](knowledge-base/04_modelo_de_datos.md) y [`knowledge-base/05_reglas_de_negocio.md`](knowledge-base/05_reglas_de_negocio.md).
  3. Este archivo (`AGENTS.md` / `CLAUDE.md`) y los modelos de dominio en `backend/app/domain/models/`.
- **Cómo revisar el resultado**:
  - Verificar que emita el dictamen estructurado con: (1) Checklist de Reglas de Negocio (`RN-AG-01`, `RN-AG-02`, `RN-GL-01`, `RN-GL-02`) y Reglas Duras (`#1` a `#13`); (2) Cobertura de los 6 casos de borde horarios (`CB-01` adyacencia `fin == inicio`, `CB-02` división entera de slots, `CB-03` estados `cancelado`/`anulado` que liberan hueco, `CB-04` solape parcial, `CB-05` corte de horarios pasados hoy según `TIMEZONE`, `CB-06` validación de rol `odontologo`); y (3) Hallazgos con comparativa **Antes vs. Después**.

---

## Integraciones Externas (Servidores MCP)

> ⚠️ Los servidores MCP son **integraciones externas de herramientas/datos**, NO skills. No deben registrarse en `.atl/skill-registry.md`.

### Servidor MCP: `playwright` (`@playwright/mcp`)

- **Propósito**: Navegación e interacción web automatizada con inspección de árboles de accesibilidad (DOM snapshots) para verificar documentación técnica viva, contratos de APIs y comportamiento de interfaces de usuario.
- **Capacidades (Herramientas que utilizamos)**:
  1. `browser_navigate`: Navega a una URL y obtiene información de la página junto a un snapshot semántico estructurado.
  2. `browser_snapshot`: Captura el árbol de accesibilidad del DOM para inspeccionar textos, encabezados, formularios y ejemplos de código.
  3. `browser_evaluate`: Ejecuta expresiones JavaScript para validar propiedades de elementos en tiempo de ejecución.
- **Momento de uso**:
  - Al explorar o diseñar un change (`/opsx:explore`, `/opsx:propose`) cuando se requiere contrastar especificaciones con documentación viva (ej. tutoriales oficiales de FastAPI para updates parciales con `PATCH` o RFCs).
  - Durante la preparación de vistas y flujos web (`C-11` a `C-15`) para verificar accesibilidad y contratos de UI.
- **Límites de acceso y privacidad con datos de prueba**:
  - **Acceso de solo lectura / inspección**: El servidor opera en un navegador aislado (`--browser msedge`); no accede a archivos sensibles locales fuera del espacio de trabajo.
  - **Protección de datos y secretos (Regla Dura #12)**: Está **estrictamente prohibido** enviar en URLs o campos de formulario datos reales de pacientes (nombres, DNI, correos, teléfonos), credenciales (`JWT_SECRET`, `DATABASE_URL`) o secretos. Usar únicamente documentación técnica pública o datos sintéticos ficticios.
- **Configuración reproducible**: Ver ejemplo sin secretos en [`mcp_config.example.json`](mcp_config.example.json) e instrucciones detalladas en [`README.md`](README.md).

---

## Roadmap de Changes

<!-- Resumen de CHANGES.md — NO duplicar el detalle completo -->

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 18 changes en 6 fases.
- **Camino crítico** (10): `C-01 → C-02 → C-03 → C-05 → C-06 → C-07 → C-08/C-09/C-10 → C-12 → C-13/C-14/C-15`.
- **Primer change**: `C-01` (foundation-setup).
- **Gates de paralelismo**: 9 (GATE 0–8).

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras

> No existe `~/.claude/CLAUDE.md` global — todas las reglas viven en este archivo.

Acá van las reglas específicas de este proyecto, derivadas de su stack (Python/FastAPI/React/TypeScript/PostgreSQL) y **confirmadas**. Son contrato; romperlas es un defecto. Formato `NUNCA X → hacer Y`:

### Stack rules (11)
1. **Python: NUNCA schema Pydantic sin `extra="forbid"`** → rechazar campos no declarados
2. **Python: NUNCA `Session.query()` legado** → usar `select()` de SQLAlchemy 2.0
3. **Python: NUNCA `async def` sin I/O real async** → preferir `def` sincrónico
4. **TypeScript/React: NUNCA `any`** → tipado estricto; `tsconfig.json` con `strict: true`
5. **TypeScript/React: NUNCA componentes en `camelCase`** → `PascalCase` (archivos y exports)
6. **TypeScript/React: NUNCA `useEffect` para data fetching** → usar `useRequest` (ahooks) / TanStack Query
7. **Tests: NUNCA mocks de DB** → base real/contenedor (Testcontainers o Docker Compose)
8. **API/REST: NUNCA verbos en paths** (`/crear-turno`) → URIs basadas en sustantivos (`/turnos`)
9. **API/REST: NUNCA `PUT` para updates parciales** → `PATCH` con `application/merge-patch+json`
10. **Docker: NUNCA imágenes sin healthcheck** → todos los servicios con healthcheck + límites
11. **Commits: NUNCA commitear sin pedirlo** → el usuario decide cuándo

### Domain rules (2)
12. **Privacidad: NUNCA usar ni almacenar datos reales de pacientes** (nombres, DNI, teléfonos, historias clínicas) en el código, tests o fixtures. Usar siempre datos sintéticos ficticios.
13. **Agenda: Todo turno debe validar y garantizar la NO superposición de horarios** tanto para el odontólogo asignado como para el sillón/box de atención.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks (consultar MCP playwright + auditar con dental-agenda-auditor)
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
