# 🦷 turnos-odontologia — Sistema de Gestión de Turnos Odontológicos

Sistema de gestión de turnos y agenda de pacientes para consultorios odontológicos en Argentina, desarrollado para la materia **Metodología I** (Tecnicatura Universitaria en Programación — UTN Regional Mendoza) aplicando la metodología **Spec-Driven Development (SDD)** con **OpenSpec** y **Active Stack**.

---

## 👥 Datos del Proyecto y Equipo

* **Proyecto:** `turnos-odontologia`
* **Materia:** Metodología I — Tecnicatura Universitaria en Programación (UTN FRM)
* **Grupo:** LocalHost
* **Integrantes:**
  * Octavio Agustín Fiore Montivero
  * Andrés Víctor Novello
  * Máximo Franco
* **Fecha:** Noviembre de 2026

---

## 📌 Estado del Proyecto y Alcance Alcanzado (TPI)

El proyecto cuenta con **17 changes completados, verificados y archivados** bajo estricto ciclo SDD (superando ampliamente el mínimo de 6 changes exigidos para 3 integrantes), cubriendo la totalidad del camino crítico de Backend y Frontend:

### ✅ Changes Completados y Archivados (17)
* **`C-01` foundation-setup**: Estructura en capas, Docker Compose, Alembic y baseline.
* **`C-02` core-models**: Modelos SQLAlchemy (Usuario, Rol, Turno, Estado, Plantilla) y migraciones.
* **`C-03` auth-jwt**: Autenticación con JWT propio, RBAC y control de acceso.
* **`C-04` password-reset-flow**: Forzado de cambio de contraseña inicial para roles clínicos.
* **`C-05` availability-engine**: Motor de cálculo de slots y plantillas horarias (auditado con skill propia).
* **`C-06` appointment-request**: Reserva de turnos con control de concurrencia y validación de reglas duras.
* **`C-07` appointment-state-machine**: Máquina de estados de turnos con transiciones permitidas.
* **`C-08` reception-agenda**: Agenda diaria unificada y gestión operativa para Recepción.
* **`C-09` dentist-agenda**: Agenda propia del profesional y marcado de asistencia (Presente/Ausente).
* **`C-10` patient-portal**: Consulta y cancelación de turnos con antelación mínima (RN-TU-04).
* **`C-11` frontend-scaffold**: Estructura SPA en React + Vite + TypeScript con router protegido y React Query.
* **`C-12` login-page**: Interfaz de autenticación y flujo mandatorio de cambio de contraseña.
* **`C-13` patient-features**: Portal web del paciente (búsqueda de turnos, reserva interactiva y mis turnos).
* **`C-14` reception-features**: Portal web de recepción (agenda global del día y ABM de plantillas horarias).
* **`C-15` dentist-features**: Portal web del odontólogo (cronograma del día y registro de presentes).
* **`C-19` ui-dark-mode-theme**: Motor de temas accesible (Dark Zinc/Carbon puro, tokens semánticos y switch cápsula).
* **`C-20` ui-responsive-accessibility**: Navegación flotante glassmórfica estilo Dynamic Island en desktop, dock inferior táctil en mobile (WCAG 2.5.5) y login clínico modernizado.

### ⏳ Changes Pendientes del Roadmap (3)
* **`C-16` seed-data-script**: Script automatizado `scripts/seed.py` para poblado inicial masivo.
* **`C-17` docker-compose-prod**: Empaquetado de producción con Nginx reverse proxy y Gunicorn multi-worker.
* **`C-18` testing-core**: Pipeline de CI en GitHub Actions y reporte de cobertura cruzada integral.

---

## 🚀 Requisitos Previos

* **Docker & Docker Compose** (versión 20.10+ recomendada).
* **Node.js** `>= 18.0.0` y `npm` (verificado con Node `v20.x` / `v24.x`).
* **Python** `>= 3.11` (únicamente si se desea ejecutar el backend fuera de Docker).

---

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/MaxiFranco05/turnos-odontologia.git
   cd turnos-odontologia
   ```

2. **Configuración de Variables de Entorno (Sin secretos):**
   El repositorio incluye el archivo de plantilla [`.env.example`](.env.example). Copiarlo a `.env` en la raíz:
   ```bash
   cp .env.example .env
   ```
   *(Las variables por defecto están listas para desarrollo local y Docker Compose).*

---

## 🏃 Puesta en Marcha (Arranque del Sistema)

### Opción A: Levantar con Docker Compose (Recomendada)

1. **Iniciar la base de datos PostgreSQL y la API FastAPI:**
   ```bash
   docker compose up -d
   ```
   *Esto levanta PostgreSQL 16 y la API de FastAPI. Las migraciones de base de datos se ejecutan automáticamente en el arranque vía Alembic.*

2. **Iniciar el Frontend (React + Vite):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *La aplicación web estará disponible en:* **`http://localhost:5173`**

---

### Opción B: Ejecución Local de Backend sin Docker

Si se dispone de PostgreSQL local en el puerto 5432:
```bash
cd backend
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Puntos de Acceso del Sistema

| Servicio / Vista | URL | Descripción |
| :--- | :--- | :--- |
| **Frontend Web** | [`http://localhost:5173`](http://localhost:5173) | Portal interactivo con portales de Recepción, Odontólogo y Paciente. |
| **Swagger UI (API Docs)** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Documentación interactiva OpenAPI con endpoints para pruebas directas. |
| **ReDoc** | [`http://localhost:8000/redoc`](http://localhost:8000/redoc) | Especificación técnica detallada de contratos REST. |
| **Healthcheck API** | [`http://localhost:8000/health/ready`](http://localhost:8000/health/ready) | Verificación de disponibilidad de API y conexión a base de datos. |

---

## 🧪 Datos Ficticios de Demostración (Credenciales de Prueba)

> 🔒 **Regla Dura #12 (Privacidad):** Todos los datos almacenados en el sistema son 100% sintéticos y ficticios.

La pantalla de inicio de sesión (`/login`) cuenta con botones de **Acceso Rápido de Demostración (1-click)** que autocompletan las credenciales reales de la base de datos:

| Rol | Correo / Identificador | Contraseña | Vistas y Funcionalidades |
| :--- | :--- | :--- | :--- |
| **Recepción** | `recepcion@clinica.com` | `Recepcion123` | Agenda diaria global, filtros por fecha/odontólogo, confirmación y anulación de turnos, gestión de plantillas horarias. |
| **Odontólogo** | `martin.ruiz@clinica.com` | `Odontologo123` | Agenda personal del día, vista cronológica de pacientes, marcado de asistencia (*Presente* / *Ausente*). |
| **Paciente** | `lucia.gomez@gmail.com` | `Paciente123` | Catálogo de turnos disponibles, reserva online con validación de antelación y cancelación autónoma. |

---

## 🧪 Ejecución de Pruebas Automatizadas (Tests)

El proyecto fue desarrollado bajo estricto **Test-Driven Development (TDD)** con una cobertura integral:

### 1. Tests de Frontend (React Testing Library + Vitest)
```bash
cd frontend
npm test -- --run
```
* **Resultado:** **26 archivos de prueba y 120/120 tests pasando en verde (100% de éxito)**.
* Comprobación de tipos y build de producción:
  ```bash
  npm run build
  ```

### 2. Tests de Backend (Pytest)
```bash
# Dentro del contenedor Docker:
docker compose exec api pytest

# O localmente con el entorno virtual activo:
python -m pytest backend/tests
```
* **Cobertura:** 17 archivos de prueba cubriendo restricciones de no-solapamiento horario (`CB-01` a `CB-06`), autenticación JWT, RBAC, máquina de estados y repositorios.

---

## 🧩 Integración de Skill Propia y Servidor MCP

Documentación académica completa de la integración en:
* **Ficha de Investigación (Parte 1):** [`docs/skills-mcp/investigacion.md`](docs/skills-mcp/investigacion.md)
* **Informe de Aplicación y Evidencias (Parte 2):** [`docs/skills-mcp/aplicacion.md`](docs/skills-mcp/aplicacion.md)

### 1. Skill Propia: `dental-agenda-auditor`
* **Ubicación en el repositorio:** [`.agents/skills/dental-agenda-auditor/SKILL.md`](.agents/skills/dental-agenda-auditor/SKILL.md)
* **Registro en la fundación:** [`.atl/skill-registry.md`](.atl/skill-registry.md), [`AGENTS.md`](AGENTS.md) y [`CLAUDE.md`](CLAUDE.md).
* **Propósito:** Creada con la asistencia de `skill-creator` para auditar artefactos OpenSpec (`proposal.md`, `design.md`, `specs/`, `tasks.md`) contra las **13 Reglas Duras** del dominio de agenda odontológica y los 6 casos de borde (`CB-01` a `CB-06`), garantizando la no-superposición de turnos por profesional y por sillón de atención.

### 2. Servidor MCP: `playwright` (`@playwright/mcp`)
* **Propósito:** Navegación e inspección automatizada de árboles de accesibilidad (DOM snapshots) y validación de UI.
* **Archivo de configuración reproducible (sin secretos):** [`mcp_config.example.json`](mcp_config.example.json)
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
* **Aplicación práctica:** Utilizado para auditar en vivo la responsividad de `C-20`, detectando y eliminando scrollbars parásitos en viewport de escritorio y pantallas angostas (iPhone SE 375x667px).

---

## 🏗️ Estructura del Repositorio

```text
turnos-odontologia/
├── .agents/skills/                # Skills locales versionadas del proyecto
│   ├── dental-agenda-auditor/     # Skill propia de auditoría de agenda clínica
│   └── ...                        # Skills del stack (fastapi, python-sqlalchemy, tdd, etc.)
├── .atl/skill-registry.md         # Registro formal de skills del proyecto
├── AGENTS.md                      # Reglas de gobierno para agentes IA
├── CLAUDE.md                      # Espejo sincronizado de AGENTS.md
├── CHANGES.md                     # Roadmap operacional con 17 changes completados y 3 pendientes
├── mcp_config.example.json        # Configuración de ejemplo sin secretos para MCP Playwright
├── docker-compose.yml             # Orquestación de servicios (api, postgres)
├── backend/                       # Backend FastAPI + SQLAlchemy 2.0 async + Alembic
│   ├── app/                       # Capas domain, application, infrastructure y api
│   ├── alembic/                   # Migraciones de base de datos PostgreSQL
│   └── tests/                     # Suite de pruebas automatizadas con pytest
├── frontend/                      # Frontend SPA React 18 + TypeScript + Vite + Tailwind
│   ├── src/                       # Componentes, layouts, portales por rol y contextos
│   └── package.json               # Dependencias de npm y scripts de build/test
├── docs/
│   ├── discovery/                 # Informe de investigación y relevamiento inicial
│   └── skills-mcp/                # Documentación formal de la Skill Propia y Servidor MCP
├── knowledge-base/                # Base de conocimiento fundacional (10 archivos canónicos)
└── openspec/                      # Especificaciones canónicas y changes SDD archivados
    ├── specs/                     # 21 especificaciones principales sincronizadas
    └── changes/archive/           # 17 changes completados y archivados bajo ciclo SDD
```
