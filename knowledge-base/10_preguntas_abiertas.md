# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — Plantilla de disponibilidad: recomendada pero no decidida en Q&A

**Documento A dice** (`docs/discovery/informe-discovery.md` §D.3): la
disponibilidad deriva de la plantilla del odontólogo.
**Checklist Q&A dice**: nada sobre plantillas; solo «vista de agenda».
**Impacto**: RN-AG-02, `PlantillaDisponibilidad` y el flujo 2 dependen de
este supuesto (SU-01).
**Resolución propuesta**: confirmar SU-01 con el consultorio antes del
Sprint 1; si se rechaza, reemplazar plantilla por carga manual de huecos.

### IN-02 — Reserva directa en huecos simples: propuesta sin origen en Q&A

**Documento A dice** (§D.3, diferenciadores v1): reserva directa inmediata
en huecos simples + solicitud a confirmar para el resto.
**Checklist Q&A dice**: todo entra como «solicitud» (recepción confirma).
**Impacto**: US-003 asume solo modo solicitud; el modo directo cambiaría
estados y permisos.
**Resolución propuesta**: mantener solo solicitud en v1 salvo pedido
explícito; registrar el modo directo como candidato v2.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| Alta | Alta-2. Confirmar `system_type = web_app` y `scale = public_multi_user` (inferidos, ver SU-02). | `state.kb.discovery` y roadmap | Usuario |
| Media | Media-1. ¿Cuántos odontólogos en la prueba inicial? (Sin definir por ahora.) ¿Uno o varios consultorios (SU-03)? | Seeds, escala | Consultorio |
