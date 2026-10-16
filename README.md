# 🦷 turnos-odontologia - Sistema de Gestión de Turnos Odontológicos

Sistema de gestión de turnos y agenda de pacientes para consultorios odontológicos en Argentina, desarrollado para la materia **Metodología I** (Tecnicatura Universitaria en Programación - UTN FRM) aplicando la metodología **Spec-Driven Development (SDD)** con **OpenSpec** y **Active Stack**.

---

## 👥 Datos del Proyecto y Equipo

* **Proyecto:** `turnos-odontologia`
* **Materia:** Metodología I – Tecnicatura Universitaria en Programación (UTN Regional Mendoza)
* **Grupo:** LocalHost
* **Integrantes:**
  * Octavio Agustín Fiore Montivero
  * Andrés Víctor Novello
  * Máximo Franco
* **Fecha:** Octubre de 2026

---

## 📌 Descripción del Proyecto

`turnos-odontologia` es una solución pensada para el mercado argentino que permite gestionar la agenda de un consultorio o clínica odontológica, previniendo solapamientos de horarios por profesional y por sillón/box de atención, además de administrar la reserva de turnos digitales.

El desarrollo del proyecto se realizó mediante el flujo de trabajo asistido por IA gobernada:
1. **Discovery:** Investigación de mercado sobre 15 sistemas odontológicos locales y de Latinoamérica para definir un MVP competitivo.
2. **Fundación Active Stack:** Definición de la Base de Conocimiento (10 archivos canónicos), Roadmap crítico (`CHANGES.md`) y Reglas de Gobierno (`AGENTS.md` y `CLAUDE.md`).
3. **Ciclo OPSX & SDD:** Especificación e implementación del Change **C-06** (`POST /turnos/solicitar`) aplicando TDD y validando 3 escenarios de prevención de superposición de turnos.

---

## 🏗️ Estructura del Repositorio

```text
turnos-odontologia/
├── .active-orchestrator-state.json # Estado de orquestación con Active Stack
├── AGENTS.md                  # Reglas del agente e instrucciones de gobierno
├── CLAUDE.md                  # Directivas de contexto para modelos de IA
├── CHANGES.md                 # Roadmap crítico de cambios (Changes)
├── README.md                  # Documentación principal del proyecto
├── Makefile                   # Automatización de compilación y pruebas
├── pyproject.toml             # Configuración de herramientas de desarrollo Python
├── docs/                      # Entregables administrativos e investigación
│   ├── discovery/
│   │   ├── informe-discovery.md  # Informe técnico de Discovery (Secciones A-D)
│   │   └── informe-discovery.pdf # Versión PDF del informe de investigación
│   └── reflexion-escrita.md   # Reflexión del grupo LocalHost e inspección metodológica
├── knowledge-base/            # Base de conocimiento (10 archivos canónicos)
├── openspec/                  # Artefactos y especificaciones de OpenSpec
│   └── changes/
│       └── archive/
│           └── C-06-appointment-request/ # Change C-06 archivado
│               ├── proposal.md
│               ├── design.md
│               ├── tasks.md
│               └── specs/
│                   └── scenarios-overlap.md
└── src/                       # Código fuente del sistema
    ├── backend/               # API REST (FastAPI, SQLAlchemy 2.0, pytest)
    │   ├── api/               # Endpoints y pruebas unitarias (test_appointment.py)
    │   └── core/              # Configuración y modelos de dominio
    └── frontend/              # Interfaz de usuario web
