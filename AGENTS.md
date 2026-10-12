# AGENTS.md — turnos-odontologia

> Instrucciones canónicas para agentes que trabajen en este proyecto.  
> Generado automáticamente desde KB + CHANGES.md + skill-registry.  
> **No editar a mano** — regenerar con `/active-orchestrator:kb` → `/active-orchestrator:rules`.

---

## Stack tecnológico (desde `knowledge-base/02_descripcion_general.md`)

| Capa | Tecnología | Estado |
|---|---|---|
| Frontend | React + TypeScript + Vite | Definido por cátedra |
| Backend | Python + FastAPI + SQLAlchemy (ORM) | Definido por cátedra |
| Base de datos | PostgreSQL | Definida por cátedra |
| Auth | JWT (correo o N.º socio + contraseña) | Definido |
| Async (futuro) | Redis (v2+) | Previsto, no usado en v1 |
| Entornos | Docker / Docker Compose | Definido por cátedra |

---

## Knowledge Base (10 archivos canónicos)

| # | Archivo | Descripción |
|---|---|---|
| 01 | `knowledge-base/01_vision_y_objetivos.md` | Visión, objetivos, alcance, métricas de éxito |
| 02 | `knowledge-base/02_descripcion_general.md` | Stack, arquitectura, integraciones, API propuesta |
| 03 | `knowledge-base/03_actores_y_roles.md` | Actores, RBAC, rutas públicas/privadas, alta de cuentas |
| 04 | `knowledge-base/04_modelo_de_datos.md` | Entidades, ERD, constraints, seed data |
| 05 | `knowledge-base/05_reglas_de_negocio.md` | Reglas de negocio (RN-AG, RN-TU, RN-AU, RN-GL) |
| 06 | `knowledge-base/06_funcionalidades.md` | User stories + criterios de aceptación (US-001 a US-012) |
| 07 | `knowledge-base/07_flujos_principales.md` | 5 flujos principales paso a paso |
| 08 | `knowledge-base/08_arquitectura_propuesta.md` | Patrones, estructura de directorios, variables de entorno |
| 09 | `knowledge-base/09_decisiones_y_supuestos.md` | Decisiones de diseño (DD-01 a DD-06) y supuestos |
| 10 | `knowledge-base/10_preguntas_abiertas.md` | Preguntas pendientes de resolución |

---

## Skills disponibles (desde `.atl/skill-registry.md`)

| Trigger / Área | Skill | Compact Rules (resumen) |
|---|---|---|
| TDD, red-green-refactor | `tdd` | Test behavior via public seams; red before green; vertical slices |
| REST API, OpenAPI, endpoints | `rest-api-guidelines` | Noun-based URIs, PATCH + merge-patch, problem+json errors |
| FastAPI, Pydantic, SSE, DI | `fastapi` | Annotated+Depends, async only when fully async, router-level config |
| Full stack, monorepo, pnpm | `fe-fullstack-dev` | web/server/packages/shared, Vite proxy, Prisma, shared types |
| Dockerize, compose, healthchecks | `docker-init` | Scan manifests first, pinned official images, healthchecks + limits |
| JWT, authentication, tokens | `jwt-auth` | Stateless, HS256/RS256, httpOnly cookies, refresh mechanism |
| Archive OpenSpec changes | `openspec-archive-change` | Prompt for change, check completion, archive with .openspec.yaml |
| SQLAlchemy 2.0, ORM, Alembic | `python-sqlalchemy` | select() not query(), Mapped+mapped_column, repo flush not commit |
| Jest, Vitest, Testing Library | `javascript-testing-patterns` | AAA, one assertion, mock externals, 80%+ coverage, factories |
| PostgreSQL search, pgvector, BM25 | `mastering-postgresql` | tsvector+GIN, HNSW for vectors, asyncpg/psycopg3 drivers |
| React 19, Vite, Tailwind, antd | `fe-react-dev-stack` | Functional only, ahooks > useEffect, services/stores separation |
| Validation, Zod, Pydantic | `loom-data-validation` | Parse don't validate, strict() at boundaries, canonicalize first |
| Persistent memory, engram | `engram-memory` | ALWAYS ACTIVE — save decisions/bugs/discoveries proactively |

---

## Roadmap — Resumen desde `CHANGES.md`

**Total:** 18 changes en 6 fases | **Camino crítico:** 10 changes | **Gates:** 9 (GATE 0–8)

### Primer change recomendado: `C-01` — foundation-setup
- Estructura directorios, pyproject.toml, package.json, Docker Compose, Alembic, scripts make
- Governance: CRITICO | Deps: ninguna

### Secuencia crítica (irreducible):
```
C-01 → C-02 → C-03 → C-05 → C-06 → C-07 → C-08/C-09/C-10 → C-12 → C-13/C-14/C-15
```

### Plan 3 agentes (resumen):
| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Frontend) |
|---|---|---|---|
| 1 | C-01 | — | — |
| 2 | C-02 | — | — |
| 3 | C-03 | C-05 | C-11 |
| 4 | C-16 | — | — |
| 5 | C-04 | — | C-12 |
| 6 | C-06 | — | — |
| 7 | C-07 | — | — |
| 8 | — | C-08 | — |
| 9 | — | C-09 | — |
| 10 | — | C-10 | — |
| 11 | C-17 | — | C-13 |
| 12 | C-18 | — | C-14 |
| 13 | — | — | C-15 |

> Ver `CHANGES.md` para detalle completo de cada change (scope, deps, governance, "Leer antes").

---

## Reglas Duras (13 total — 11 stack + 2 dominio)

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

## Referencia global
No se encontró CLAUDE.md global en `~/.config/opencode/` ni `~/.claude/`.  
Todas las reglas del proyecto viven en este archivo.

---

## Workflow

### Para iniciar trabajo en un change:
1. Leer `CHANGES.md` → identificar change (ej. `C-03`)
2. Leer archivos listados en **Leer antes** de ese change
3. Ejecutar `/opsx:propose C-03-nombre` para generar spec OpenSpec
4. Implementar según spec + correr tests
5. Archivar con `/opsx:archive C-03-nombre`
6. Marcar `[x]` en `CHANGES.md`

### Convenciones de commits:
- Formato: `tipo(scope): descripción` (conventional commits)
- Tipos: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
- **Nunca commitear sin confirmación explícita del usuario** (Regla 11)

### Testing:
- Unitarios: repositorios, servicios, máquinas de estado
- Integración: flujos E2E API (login → solicitar → confirmar → marcar presente)
- Contratos: validación schema OpenAPI
- Frontend: React Testing Library
- Cobertura objetivo: 80% en `domain/` y `application/`
- **BD real en contenedor** (Regla 7) — no mocks

### Despliegue:
- Docker Compose con healthchecks en todos los servicios (Regla 10)
- Variables sensibles via `.env` (nunca en repo)
- Multi-stage Dockerfiles, non-root user

---

*Generado: 2026-10-12 — v1.0*