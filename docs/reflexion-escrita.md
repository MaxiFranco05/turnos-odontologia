# REFLEXIÓN ESCRITA: TRABAJO INTEGRADOR METODOLOGÍA I
**Proyecto:** Sistema de Gestión de Turnos Odontológicos (`turnos-odontologia`)
**Materia:** Metodología I — Tecnicatura Universitaria en Programación (UTN FRM)
**Grupo:** LocalHost
**Integrantes:**
- Octavio Agustín Fiore Montivero
- Andrés Víctor Novello
- Máximo Franco
**Fecha:** Octubre de 2026

### 1. Detección de Información Incorrecta o Inventada en Discovery
Durante la investigación de mercado con `discovery-research`, la IA tendía a asumir integraciones no demostradas (ej. AFIP o Mercado Pago en todos los planes). Para no fundamentar el MVP en datos falsos, auditamos manualmente las URLs oficiales y marcamos como **"No evidenciado"** toda función sin prueba pública explícita.

### 2. Aplicación del Protocolo de Inspección: "Ajustar" vs. "Continuar"
- **En Reglas (`AGENTS.md`):** Seleccionamos **Ajustar** para añadir reglas estrictas del dominio: prohibición de superposición de turnos por odontólogo y sillón, restricción de datos reales de pacientes, y uso estricto de SQLAlchemy 2.0.
- **En Change C-06 (`POST /turnos/solicitar`):** Al revisar `Propose`, notamos que la propuesta obviaba solapamientos parciales. Seleccionamos **Ajustar** para exigir en `specs/` tres escenarios: feliz, fuera de horario y superposición parcial.
- **Consecuencia de Continuar:** Hubiéramos implementado un backend defectuoso que permite turnos duplicados.

### 3. Especificación Aprobada (SDD) vs. Prompts Sueltos
Con prompts sueltos la IA improvisa endpoints y sintaxis obsoleta. Con Spec-Driven Development, la fase `Apply` actuó como contrato cerrado: el código generado pasó a **GREEN** en `pytest` en la primera ejecución.

### 4. Evaluación de Valor de la Fundación
- **Mayor valor:** `AGENTS.md` y `knowledge-base/` actuaron como un arnés estricto de arquitectura.
- **Menor valor:** El roadmap extendido `CHANGES.md` para cambios lejanos no impactó directamente en C-06.

### 5. Memoria Persistente (Engram) y Trazabilidad
La consulta a Engram demostró la recuperación del contexto (reglas del stack, reestructuración `src/backend` y modelo de C-06) entre sesiones. Los conflictos en estado *Pending* evidenciaron cómo Engram detecta actualizaciones superpuestas de contexto.

### 6. Distribución de Tareas del Equipo (Grupo LocalHost)
- **Octavio Agustín Fiore Montivero:** Responsable del ciclo OPSX del Change C-06 (diseño TDD, endpoints y reglas anti-solapamiento) y reestructuración `src/backend/`.
- **Andrés Víctor Novello:** Responsable del estudio de mercado Discovery, matriz de evaluación y verificación de fuentes oficiales.
- **Máximo Franco:** Responsable de la orquestación inicial de OpenSpec, base de conocimiento y orquestación del roadmap.
