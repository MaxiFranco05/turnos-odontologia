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
* **Fecha:** Noviembre de 2026

---

## 📌 Descripción del Proyecto

`turnos-odontologia` es una solución pensada para el mercado argentino que permite gestionar la agenda de un consultorio o clínica odontológica, previniendo solapamientos de horarios por profesional y por sillón/box de atención, además de administrar la reserva de turnos digitales.

El desarrollo del proyecto se realiza mediante el flujo de trabajo asistido por IA gobernada:
1. **Discovery:** Investigación de mercado sobre sistemas odontológicos locales y de Latinoamérica para definir un MVP competitivo.
2. **Fundación Active Stack:** Definición de la Base de Conocimiento (10 archivos canónicos en `knowledge-base/`), Roadmap crítico (`CHANGES.md`), Registro de Skills (`.atl/skill-registry.md`) y Reglas de Gobierno (`AGENTS.md` y `CLAUDE.md`).
3. **Ciclo OPSX & SDD:**
   - Changes implementados, testeados y archivados: `C-01` (`foundation-setup`), `C-02` (`core-models`), `C-03` (`auth-jwt`), `C-04` (`password-reset-flow`) y `C-11` (`frontend-scaffold`).
   - Incorporación de la skill propia `dental-agenda-auditor` y del servidor MCP `playwright` para la preparación SDD del change pendiente **`C-05` (`c-05-availability-engine`)**.

---

## 🧩 Integración de Skill Propia y Servidor MCP

Documentación completa del trabajo práctico en:
- **Ficha de Investigación (Parte 1):** [`docs/skills-mcp/investigacion.md`](docs/skills-mcp/investigacion.md)
- **Informe de Aplicación y Evidencias (Parte 2):** [`docs/skills-mcp/aplicacion.md`](docs/skills-mcp/aplicacion.md)

### 1. Skill Propia (`dental-agenda-auditor`) y Skill Creadora (`skill-creator`)

- **Ubicación versionada en el repositorio:** [`.agents/skills/dental-agenda-auditor/SKILL.md`](.agents/skills/dental-agenda-auditor/SKILL.md)
- **Registro en la fundación:** [`.atl/skill-registry.md`](.atl/skill-registry.md), [`AGENTS.md`](AGENTS.md) y [`CLAUDE.md`](CLAUDE.md).
- **Reproducción de la skill creadora (`skill-creator`)**:
  En el equipo de trabajo ya estaba instalada globalmente en `~/.gemini/config/skills/skill-creator/SKILL.md` (fuera del repo). Para instalarla en otro equipo, seguir las instrucciones del repositorio oficial https://github.com/anthropics/skills (carpeta `skills/skill-creator`). Comando sugerido, **pendiente de verificar** contra esa fuente:
  ```bash
  npx skills add anthropics/skills --skill skill-creator
  ```
  Comprobación: el archivo `SKILL.md` debe existir en la carpeta de skills del agente y la skill debe aparecer en la lista de skills disponibles.
  *(La skill propia `dental-agenda-auditor` ya está versionada en `.agents/skills/dental-agenda-auditor/SKILL.md`; al clonar o hacer `git pull` queda disponible para el agente sin instalación adicional).*

### 2. Servidor MCP (`playwright` — `@playwright/mcp`)

El proyecto integra el servidor MCP oficial de Microsoft **Playwright** (`@playwright/mcp`) para navegación web automatizada, inspección de documentación técnica en vivo y extracción de árboles semánticos de accesibilidad (DOM snapshots) durante el diseño y preparación de changes.

#### Requisitos previos
- **Node.js** `>= 18.0.0` y `npx` disponibles en el `PATH` (`node --version && npx --version`). Verificado en el equipo con Node `v24.19.0` / npx `11.17.0`.
- Navegador compatible instalado (Microsoft Edge en Windows o Google Chrome / Chromium).

#### Variables de entorno
- **Ninguna.** El servidor funciona de manera autónoma sin requerir claves de API, tokens ni credenciales de base de datos.

#### Pasos de configuración reproducible
1. En la raíz del repositorio se incluye el archivo de ejemplo sin secretos [`mcp_config.example.json`](mcp_config.example.json):
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
2. Copiar o fusionar el bloque `mcpServers.playwright` en el archivo de configuración MCP del cliente:
   - **Antigravity (configuración global del usuario, fuera del repo):** `~/.gemini/config/mcp_config.json` (en Windows: `C:\Users\<Usuario>\.gemini\config\mcp_config.json`).
   - **Otros clientes (Claude Code / Cursor):** archivo MCP propio de cada cliente según su documentación (p. ej. `.mcp.json` o `.cursor/mcp.json` en la raíz del workspace).
3. Reiniciar o recargar las herramientas MCP en el agente.

#### Comprobación de conexión y ejecución de prueba
1. Comprobar que el servidor `playwright` aparece conectado y expone herramientas como `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_evaluate`, etc.
2. Pedir al agente o ejecutar vía JSON-RPC:
   > *"Usá la herramienta `browser_navigate` de `playwright` para navegar a `https://fastapi.tiangolo.com/tutorial/body-updates/` e inspeccionar el árbol de accesibilidad sobre actualizaciones parciales con PATCH."*
3. Resultado esperado: el servidor navega exitosamente y emite el snapshot semántico de la página. Evidencia real de esta ejecución: [`docs/skills-mcp/evidencias/evidencia-mcp-playwright.md`](docs/skills-mcp/evidencias/evidencia-mcp-playwright.md).

#### Problemas encontrados y prevención
- **Detección de Chrome en Windows:** Playwright busca por defecto el binario de Chrome en `AppData\Local\Google\Chrome\Application\chrome.exe`. Si Chrome no está en esa ruta, falla solicitando instalarlo.
  - **Solución implementada:** Se configuró el argumento `--browser msedge`, que aprovecha el navegador Microsoft Edge preinstalado en el sistema operativo Windows, asegurando una ejecución reproducible inmediata y sin descargas pesadas adicionales.
- **Prevención de ENOENT en Windows:** Si un cliente MCP en Windows informa `spawn npx ENOENT`, reemplazar `"command": "npx"` por `"command": "cmd"` y anteponer `"/c", "npx"` a los `args`.

---

## 🏗️ Estructura del Repositorio

```text
turnos-odontologia/
├── .agents/skills/                # Skills locales versionadas del proyecto
│   ├── dental-agenda-auditor/     # Skill propia de auditoría de agenda y turnos (RN-AG/RN-TU)
│   └── ...                        # Skills del stack (fastapi, python-sqlalchemy, tdd, etc.)
├── .atl/skill-registry.md         # Registro de skills y Compact Rules para subagentes
├── AGENTS.md                      # Reglas del agente, skills por rol e integraciones MCP
├── CLAUDE.md                      # Espejo sincronizado de AGENTS.md
├── CHANGES.md                     # Roadmap crítico de 18 changes en 6 fases
├── mcp_config.example.json        # Configuración de ejemplo sin secretos para el MCP Playwright
├── docker-compose.yml             # Orquestación local (api, postgres, redis)
├── backend/                       # API REST (FastAPI, SQLAlchemy 2.0 async, Alembic, pytest)
│   ├── app/                       # Capas domain, application, infrastructure y api
│   └── tests/                     # Suite de integración contra base de datos real
├── frontend/                      # SPA React 18 + TypeScript + Vite + Tailwind + TanStack Query
├── docs/
│   ├── discovery/                 # Informe técnico de Discovery
│   └── skills-mcp/                # Ficha de investigación e informe de aplicación (Skill + MCP)
├── knowledge-base/                # Base de conocimiento (10 archivos canónicos)
└── openspec/                      # Artefactos y especificaciones SDD de OpenSpec
    ├── specs/                     # Especificaciones principales sincronizadas
    └── changes/
        ├── archive/               # Changes completados y archivados (C-01 a C-04, C-11)
        └── c-05-availability-engine/ # Change C-05 preparado (proposal, design, specs, tasks)
```
