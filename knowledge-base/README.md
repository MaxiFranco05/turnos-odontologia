# turnos-odontologia — Base de Conocimiento

Base de conocimiento generada por ingesta de `docs/discovery/informe-discovery.md`
+ sección `discovery` de `.active-orchestrator-state.json` (fuente: `ingest`,
sin preguntas; lo no inferible está en `10_preguntas_abiertas.md`).

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v1, fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack cátedra (FastAPI+React+Postgres, JWT, Redis futuro), arquitectura lógica, sin integraciones, API propuesta |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Paciente/recepción/odontólogo, matriz RBAC, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Usuario, PlantillaDisponibilidad, Turno; anti-solape; seeds sin valores |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-AU/TU/AG/GL con trazabilidad |
| [06_funcionalidades.md](06_funcionalidades.md) | 4 épicas, US-001…US-009 con criterios y reglas |
| [07_flujos_principales.md](07_flujos_principales.md) | Login, solicitud, confirmación, presente/ausente, ausentismo |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, directorios, seguridad, env vars (propuesta) |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01…DD-05, SU-01…SU-04 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | IN-01/IN-02, 10 preguntas priorizadas (stack bloqueante) |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

Sistema de turnos odontológicos que reemplaza WhatsApp/papel con reserva
online, agenda por odontólogo y estados por rol; v1 sin integraciones, con
anti-solapamiento de servidor como diferencial, sobre FastAPI + React +
PostgreSQL (Redis reservado a v2+).
