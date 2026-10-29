# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto turnos-odontologia.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificá el change a implementar (ej. `C-03`).
2. Leé los archivos listados en **Leer antes** para contexto y contratos.
3. Ejecutá `/opsx:propose C-03-auth-jwt` para generar la spec OpenSpec.
4. Implementá según la spec y corré tests.
5. Archivá con `/opsx:archive C-03-auth-jwt`.
6. Marcá el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-setup
└── C-02 core-models
    ├── C-03 auth-jwt
    │   ├── C-04 password-reset-flow
    │   ├── C-06 appointment-request
    │   │   └── C-07 appointment-state-machine
    │   │       ├── C-08 reception-agenda
    │   │       ├── C-09 dentist-agenda
    │   │       └── C-10 patient-portal
    │   └── C-12 login-page (needs C-11)
    ├── C-05 availability-engine
    │   └── C-06 appointment-request
    ├── C-16 seed-data-script
    └── C-11 frontend-scaffold
        └── C-12 login-page
            ├── C-13 patient-features (needs C-05, C-06, C-10)
            ├── C-14 reception-features (needs C-08)
            └── C-15 dentist-features (needs C-09)
```

### Paralelismo por fase

**GATE 0: C-01 foundation-setup ✓** ← PRIMER FORK
  → C-02 core-models                         [Agente A - Backend Core]

**GATE 1: C-02 core-models ✓**
  → C-03 auth-jwt                            [Agente A - Backend Core]
  → C-05 availability-engine                 [Agente B - Backend Aux]
  → C-16 seed-data-script                    [Agente A - Backend Core]
  → C-11 frontend-scaffold                   [Agente C - Frontend]

**GATE 2: C-03 auth-jwt ✓ + C-11 frontend-scaffold ✓**
  → C-04 password-reset-flow                 [Agente A - Backend Core]
  → C-12 login-page                          [Agente C - Frontend]

**GATE 3: C-05 availability-engine ✓ + C-03 auth-jwt ✓**
  → C-06 appointment-request                 [Agente A - Backend Core]

**GATE 4: C-06 appointment-request ✓**
  → C-07 appointment-state-machine           [Agente A - Backend Core]

**GATE 5: C-07 appointment-state-machine ✓ + C-03 auth-jwt ✓**
  → C-08 reception-agenda                    [Agente B - Backend Aux]
  → C-09 dentist-agenda                      [Agente B - Backend Aux]
  → C-10 patient-portal                      [Agente B - Backend Aux]

**GATE 6: C-12 login-page ✓ + C-08/C-09/C-010 ✓** ← FORK (3 ramas frontend)
  → C-13 patient-features                    [Agente C - Frontend — si C-05, C-06, C-10 ✓]
  → C-14 reception-features                  [Agente C - Frontend — si C-08 ✓]
  → C-15 dentist-features                    [Agente C - Frontend — si C-09 ✓]

**GATE 7: C-01 foundation-setup ✓ (independiente)**
  → C-17 docker-compose-prod                 [Agente A - Backend Core]

**GATE 8: C-03, C-06, C-07 ✓ (núcleo funcional listo)**
  → C-18 testing-core                        [Agente A/B/C - Cross]

### Camino crítico (10 changes — mínimo irreducible)

`C-01` → `C-02` → `C-03` → `C-05` → `C-06` → `C-07` → `C-08`*`/` `C-09`*`/` `C-10`* → `C-12` → `C-13`/`C-14`/`C-15`

*Los tres changes de agenda (C-08, C-09, C-10) son intercambiables como último paso backend del camino crítico; el frontend necesita los tres para MVP completo.

### Plan óptimo con 3 agentes

| Paso | Agente A (Backend Core)         | Agente B (Backend Aux)        | Agente C (Frontend)          |
|------|--------------------------------|------------------------------|-----------------------------|
| 1    | C-01 foundation-setup          | —                            | —                           |
| 2    | C-02 core-models               | —                            | —                           |
| 3    | C-03 auth-jwt                  | C-05 availability-engine     | C-11 frontend-scaffold      |
| 4    | C-16 seed-data-script          | —                            | —                           |
| 5    | C-04 password-reset-flow       | —                            | C-12 login-page             |
| 6    | C-06 appointment-request       | —                            | —                           |
| 7    | C-07 appointment-state-machine | —                            | —                           |
| 8    | —                              | C-08 reception-agenda        | —                           |
| 9    | —                              | C-09 dentist-agenda          | —                           |
| 10   | —                              | C-10 patient-portal          | —                           |
| 11   | C-17 docker-compose-prod       | —                            | C-13 patient-features       |
| 12   | C-18 testing-core              | —                            | C-14 reception-features     |
| 13   | —                              | —                            | C-15 dentist-features       |

---

## FASE 1 — Foundation & Infra

### [C-01] `foundation-setup`
- **Estado**: [x] completado (archivado 2026-10-27)
- **Scope**:
  - Estructura de directorios: `backend/app/{domain,application,infrastructure,api}`, `frontend/src/{features,shared,pages}`, `docker-compose.yml`
  - `pyproject.toml` / `requirements.txt`: FastAPI, SQLAlchemy, Alembic, Pydantic, python-jose, passlib, uvicorn, psycopg2
  - `package.json`: React 18, TypeScript, Vite, React Router, TanStack Query, Zod, Axios
  - Docker Compose: `api` (FastAPI), `postgres` (15+), `redis` (opcional v2+), healthchecks
  - Variables de entorno: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `CANCEL_MIN_HOURS=24`, `TIMEZONE=America/Argentina/Buenos_Aires`
  - Configuración Alembic + migración inicial vacía (baseline)
  - Scripts `make dev`, `make test`, `make lint` (ruff + mypy + eslint)
- **Dependencias**: ninguna
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Variables de entorno
  - `knowledge-base/04_modelo_de_datos.md` §Entidades (para anticipar modelos)

### [C-02] `core-models`
- **Estado**: [x] completado (archivado 2026-10-27)
- **Scope**:
  - Modelos SQLAlchemy: `Usuario`, `PlantillaDisponibilidad`, `Turno` (con enum `EstadoTurno`)
  - Mixins: `TimestampMixin` (creado_en, actualizado_en), `UUIDMixin` si se usa UUID
  - Relaciones y constraints definidas en KB: FKs, unique constraints, check constraints (`hora_fin > hora_inicio`, `duracion_slot_minutos > 0`, `fin > inicio`)
  - Índices: `(odontologo_id, inicio)`, `(paciente_id, inicio)`
  - Migración Alembic `001_create_core_tables.py` con todas las tablas y constraints
  - Repositorios base genéricos (`BaseRepository`) en `domain/repositories/`
  - Tests: creación de instancias, constraints de integridad, anti-solape a nivel DB (unique partial index o trigger)
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Entidades, §ERD, §Seed data inicial
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01, §RN-TU-05
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (invariante de servidor)

---

## FASE 2 — Auth & Access Control

### [C-03] `auth-jwt`
- **Estado**: [x] completado (archivado 2026-10-29)
- **Scope**:
  - `POST /api/auth/login` — acepta `identificador` (email o nro_socio) + `password`; retorna `access_token` (JWT) + `refresh_token` (opcional v1)
  - Claims JWT: `sub` (user_id), `rol`, `exp`; expiración configurable `JWT_EXPIRE_MINUTES`
  - Hash de contraseñas: bcrypt via `passlib`
  - Middleware/dependencia FastAPI `get_current_user` que valida token y carga `Usuario` en `request.state.user`
  - Dependencia `require_roles(*roles)` para RBAC en endpoints
  - Rate limiting básico en login: 5 req/60s por IP+identificador
  - Tests: login exitoso con email y con nro_socio, credencial inválida (mensaje genérico), token expirado, rol incorrecto en endpoint protegido
- **Dependencias**: `C-02`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC, §Rutas públicas
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AU-01, §RN-AU-02
  - `knowledge-base/06_funcionalidades.md` US-001, US-010
  - `knowledge-base/07_flujos_principales.md` Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad

### [C-04] `password-reset-flow`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoint `POST /api/auth/cambiar-password` — requiere `debe_cambiar_password=true`; valida contraseña actual + nueva; apaga flag y actualiza `perfil_completo` si datos mínimos presentes
  - Middleware/guarda en frontend: intercepta 403/400 "password_change_required" y redirige a página de cambio obligatorio
  - Validación de fortaleza de contraseña (mín 8 chars, 1 mayúscula, 1 número)
  - Tests: flujo completo primera vez, flag persiste hasta cambio, bloqueo de otras operaciones mientras flag activo
- **Dependencias**: `C-03`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Alta de cuentas
  - `knowledge-base/06_funcionalidades.md` US-010
  - `knowledge-base/07_flujos_principales.md` Flujo 1 (pasos 18-19)

---

## FASE 3 — Availability & Appointment Core

### [C-05] `availability-engine`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - CRUD `PlantillaDisponibilidad` (solo recepción): `POST/GET/PUT/DELETE /api/plantillas` con validación de solape de plantillas del mismo odontólogo
  - `GET /api/disponibilidad?odontologo_id=&fecha=` — calcula huecos libres derivando de plantilla del día menos turnos vigentes (`solicitado`, `confirmado`) del odontólogo
  - Algoritmo: slots = plantilla slots - turnos ocupados; respeta `duracion_slot_minutos`
  - Validación `RN-AG-02`: solo horarios futuros, dentro de plantilla vigente
  - Tests: plantilla CRUD, cálculo huecos con/sin turnos, solape plantillas, fecha pasada rechaza
- **Dependencias**: `C-02`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §PlantillaDisponibilidad
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01, §RN-AG-02
  - `knowledge-base/06_funcionalidades.md` US-002
  - `knowledge-base/07_flujos_principales.md` Flujo 2 (pasos 1-2)
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (derivación plantilla → huecos)

### [C-06] `appointment-request`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `POST /api/turnos` — body: `odontologo_id`, `inicio`, `fin`, `motivo`; crea `Turno` en estado `solicitado`, `origen=online`
  - Transacción: `SELECT FOR UPDATE` en turnos del odontólogo + re-check solape (RN-AG-01) antes de insert
  - Retorna turno creado con `id`, `estado=solicitado`, `origen=online`
  - Validaciones: horario dentro de plantilla, futuro, motivo obligatorio, paciente autenticado (rol paciente)
  - Tests: solicitud exitosa, rechazo por solape concurrente, rechazo horario fuera plantilla, rechazo rol no paciente
- **Dependencias**: `C-02`, `C-03`, `C-05`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Turno, §Constraints anti-solape
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01, §RN-TU-01
  - `knowledge-base/06_funcionalidades.md` US-003
  - `knowledge-base/07_flujos_principales.md` Flujo 2 (pasos 3-5)
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (invariante de servidor)

### [C-07] `appointment-state-machine`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Enum `EstadoTurno`: `solicitado`, `confirmado`, `anulado`, `cancelado`, `presente`, `ausente`
  - Matriz de transiciones por rol (validación en servidor):
    - Paciente: `solicitado` → `cancelado` (solo propios, anticipación ≥ 24h)
    - Recepción: `solicitado` → `confirmado` | `anulado` (todos, anticipación ≥ 24h para anular)
    - Odontólogo: `confirmado` → `presente` | `ausente` (solo propios)
  - Endpoints de transición:
    - `PATCH /api/turnos/{id}/confirmar` (recepción)
    - `PATCH /api/turnos/{id}/anular` (recepción)
    - `PATCH /api/turnos/{id}/cancelar` (paciente)
    - `PATCH /api/turnos/{id}/marcar-presente` (odontólogo)
    - `PATCH /api/turnos/{id}/marcar-ausente` (odontólogo)
  - Cada endpoint valida rol, propiedad del turno, anticipación (para cancelar/anular), estado origen válido
  - Tests: matriz completa de transiciones válidas/inválidas, autorización cruzada (403), anticipación mínima
- **Dependencias**: `C-06`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Turno.estado, §Constraints transiciones
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-01 a RN-TU-05, §RN-GL-01
  - `knowledge-base/06_funcionalidades.md` US-004, US-006, US-008
  - `knowledge-base/07_flujos_principales.md` Flujos 3, 4, 5

---

## FASE 4 — Role-specific Views & Actions

### [C-08] `reception-agenda`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /api/agenda/dia?fecha=` — retorna todos los turnos del día con: paciente (nombre, contacto), odontólogo, inicio, fin, motivo, estado, origen
  - Filtro opcional por `odontologo_id`
  - Solo accesible por rol `recepcion`
  - Tests: agenda día completo, filtro por odontólogo, incluye turnos `cancelado` (origen online), 403 para otros roles
- **Dependencias**: `C-03`, `C-07`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC fila Recepción
  - `knowledge-base/06_funcionalidades.md` US-005, US-006
  - `knowledge-base/07_flujos_principales.md` Flujo 3

### [C-09] `dentist-agenda`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /api/mis-turnos?fecha=` — retorna turnos del odontólogo autenticado para la fecha
  - Solo accesible por rol `odontologo`; filtro automático por `odontologo_id = current_user.id`
  - Tests: solo muestra propios, 403 para otros roles, estados correctos
- **Dependencias**: `C-03`, `C-07`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC fila Odontólogo
  - `knowledge-base/06_funcionalidades.md` US-007, US-008
  - `knowledge-base/07_flujos_principales.md` Flujo 4

### [C-10] `patient-portal`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /api/mis-turnos?fecha_desde=&fecha_hasta=` — turnos del paciente autenticado en rango
  - `PATCH /api/turnos/{id}/cancelar` — ya cubierto en C-07, expuesto aquí como acción de paciente
  - Solo accesible por rol `paciente`
  - Tests: lista mis turnos, no ve ajenos, cancelar respeta anticipación
- **Dependencias**: `C-03`, `C-07`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC fila Paciente
  - `knowledge-base/06_funcionalidades.md` US-004
  - `knowledge-base/07_flujos_principales.md` Flujo 5

---

## FASE 5 — Frontend

### [C-11] `frontend-scaffold`
- **Estado**: `[x]` completado
- **Scope**:
  - Vite + React 18 + TypeScript configurado
  - Estructura `src/{features,shared,pages}` + `main.tsx`, `App.tsx`, `router.tsx`
  - Cliente API Axios con interceptors: adjunta JWT, maneja 401 → redirect `/login`, 403 → toast "Sin permisos"
  - TanStack Query provider + configuración global
  - Componentes base compartidos: `Button`, `Input`, `Select`, `Card`, `Table`, `Toast`, `LoadingSpinner`
  - Layouts: `AuthLayout` (login), `AppLayout` (sidebar por rol, header con usuario)
  - Tests: build ok, routing smoke, interceptors adjuntan token
- **Dependencias**: `C-01`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios frontend
  - `knowledge-base/03_actores_y_roles.md` §Rutas públicas

### [C-12] `login-page`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Página `/login` con formulario: identificador (email o nro_socio), password, checkbox "Recordar"
  - Submit → `POST /api/auth/login`; guarda tokens en `localStorage` (access) + `httpOnly cookie` (refresh si se usa)
  - Redirige según rol: `/paciente` | `/recepcion` | `/odontologo`
  - Manejo error genérico "Credenciales inválidas" (no revela existencia)
  - Si respuesta indica `password_change_required` → redirige a `/cambiar-password`
  - Tests: login exitoso cada rol, error genérico, redirect por rol, flujo password change
- **Dependencias**: `C-03`, `C-11`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Rutas públicas
  - `knowledge-base/06_funcionalidades.md` US-001, US-010
  - `knowledge-base/07_flujos_principales.md` Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend

### [C-13] `patient-features`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Página `/paciente/disponibilidad` — selector odontólogo + fecha (calendario), llama `GET /api/disponibilidad`, muestra grid de huecos libres
  - Página `/paciente/solicitar/:slotId` — modal confirmación con campo `motivo`, `POST /api/turnos`
  - Página `/paciente/mis-turnos` — lista turnos futuros/pasados con badges de estado, botón "Cancelar" (si futuro y ≥ 24h) → `PATCH /api/turnos/{id}/cancelar`
  - Navegación en `AppLayout` paciente: "Buscar turno", "Mis turnos"
  - Tests: flujo completo solicitar → ver en mis turnos → cancelar (si aplica)
- **Dependencias**: `C-05`, `C-06`, `C-10`, `C-12`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` US-002, US-003, US-004
  - `knowledge-base/07_flujos_principales.md` Flujo 2, Flujo 5
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios frontend

### [C-14] `reception-features`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Página `/recepcion/agenda` — vista día (selector fecha), tabla con todos los turnos: paciente, odontólogo, hora, motivo, estado, origen, acciones
  - Acciones por fila: "Confirmar" (si `solicitado`) → `PATCH /confirmar`, "Anular" (si `solicitado`/`confirmado`) → `PATCH /anular` con confirmación anticipación
  - Página `/recepcion/plantillas` — CRUD plantillas por odontólogo (lista, crear, editar, eliminar)
  - Navegación recepción: "Agenda del día", "Plantillas"
  - Tests: agenda carga, confirmar/anular cambian estado, plantillas CRUD
- **Dependencias**: `C-08`, `C-12`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` US-005, US-006
  - `knowledge-base/07_flujos_principales.md` Flujo 3
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios frontend

### [C-15] `dentist-features`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Página `/odontologo/agenda` — vista día (selector fecha), lista solo sus turnos con paciente, hora, motivo, estado
  - Acciones por fila: "Marcar presente" / "Marcar ausente" (si `confirmado`) → `PATCH /marcar-presente|ausente`
  - Navegación odontólogo: "Mi agenda"
  - Tests: solo ve propios, marcar presente/ausente funciona, 403 si intenta turno ajeno
- **Dependencias**: `C-09`, `C-12`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` US-007, US-008
  - `knowledge-base/07_flujos_principales.md` Flujo 4
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios frontend

---

## FASE 6 — Polish & Production Readiness

### [C-16] `seed-data-script`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Script `scripts/seed.py` (o management command) que carga:
    - Catálogo de estados de turno (id, nombre, descripción)
    - Usuario recepción (email, password temporal, rol=recepcion, debe_cambiar_password=true)
    - Usuarios odontólogos de la prueba inicial (cantidad según Q&A, ver `10_preguntas_abiertas.md`)
    - Plantillas de disponibilidad iniciales por odontólogo (lunes-viernes 9-13, 14-18, slot 30 min)
    - Valor `CANCEL_MIN_HOURS=24` en config/DB
  - Idempotente: re-ejecutable sin duplicados
  - Tests: script corre sin errores, datos consultables via API
- **Dependencias**: `C-02`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/10_preguntas_abiertas.md` §Media-1

### [C-17] `docker-compose-prod`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `docker-compose.prod.yml`: api (gunicorn + workers), postgres, nginx reverse proxy, certbot (opcional)
  - Variables de entorno separadas `.env.prod` (secrets fuera del repo)
  - Healthchecks y restart policies
  - Build multi-stage Dockerfile para backend y frontend
  - Tests: `docker compose -f docker-compose.prod.yml up` levanta todo, healthchecks pasan
- **Dependencias**: `C-01`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Variables de entorno

### [C-18] `testing-core`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Tests unitarios: repositorios, servicios de disponibilidad, máquina de estados
  - Tests de integración: flujos E2E API (login → solicitar → confirmar → marcar presente)
  - Tests de contratos: OpenAPI schema validation
  - Cobertura mínima objetivo: 80% en `domain/` y `application/`
  - CI pipeline (GitHub Actions): lint + typecheck + tests + build docker
  - Tests frontend: React Testing Library para login, disponibilidad, agenda
- **Dependencias**: `C-03`, `C-06`, `C-07`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` (todos los CA)
  - `knowledge-base/07_flujos_principales.md` (todos los flujos)
  - `knowledge-base/05_reglas_de_negocio.md` (todas las RN)

---

## Resumen

✅ `CHANGES.md` creado en la raíz con **18 changes** organizados en **6 fases**.

**Camino crítico**: 10 changes
**Gates de paralelismo**: 9 (GATE 0–8)
**Primer change recomendado**: `C-01` (foundation-setup)

Para arrancar: `/opsx:propose C-01-foundation-setup`