# Spec Delta

## Purpose

Define los contratos de verificación automatizada de integración de extremo a extremo (E2E), auditoría estricta de contratos OpenAPI según las reglas de arquitectura REST, y ejecución del pipeline de Integración Continua (CI).

## ADDED Requirements

### Requirement: End-to-End Clinical Appointment Lifecycle Validation
El sistema SHALL proveer suites de pruebas de integración E2E que validen de forma secuencial y transaccional los flujos clínicos completos de reserva, confirmación, asistencia y cancelación entre múltiples actores utilizando datos sintéticos ficticios.

#### Scenario: Happy path complete appointment lifecycle across all roles
- **WHEN** un paciente solicita un turno disponible, recepción lo confirma en su agenda del día, y el odontólogo asignado marca presente
- **THEN** cada transición de estado tiene éxito secuencial (solicitado -> confirmado -> presente), actualizando la base de datos y bloqueando cancelaciones posteriores con 409 Conflict.

#### Scenario: Early patient cancellation releases slot back to availability
- **WHEN** un paciente cancela su turno reservado con más de 24 horas de anticipación
- **THEN** el turno transiciona a cancelado y el hueco horario vuelve a figurar como libre en el endpoint de disponibilidad para nuevas solicitudes.

#### Scenario: Late cancellation within minimum window rejected with 422
- **WHEN** un paciente intenta cancelar un turno dentro de la ventana de anticipación mínima de 24 horas
- **THEN** la API rechaza la cancelación con código HTTP 422 Unprocessable Entity y el turno permanece en su estado confirmado.

#### Scenario: Overlapping booking request rejected with 409 conflict
- **WHEN** un segundo paciente intenta solicitar un turno en el mismo intervalo horario y con el mismo odontólogo que un turno ya solicitado o confirmado
- **THEN** la API rechaza la solicitud concurrente con código HTTP 409 Conflict, preservando la invariante anti-solape de la Regla Dura #13.

#### Scenario: Cross-dentist attendance mutation rejected with 403
- **WHEN** un odontólogo autenticado intenta marcar asistencia sobre un turno asignado a otro profesional
- **THEN** la API rechaza la solicitud con código HTTP 403 Forbidden preservando la integridad del registro clínico.

### Requirement: OpenAPI Contract and REST Hard Rules Compliance
El contrato de la API expuesto por FastAPI SHALL ser validado programáticamente contra los estándares de diseño REST del proyecto, garantizando el cumplimiento irrestricto de las Reglas Duras #8 y #9.

#### Scenario: Valid OpenAPI 3 specification generation
- **WHEN** se extrae el esquema OpenAPI (`/openapi.json`) de la aplicación
- **THEN** genera una especificación OpenAPI 3.x válida con componentes, esquemas de seguridad Bearer JWT y esquemas de respuesta estandarizados.

#### Scenario: Strict noun-based URIs without action verbs
- **WHEN** se auditan las rutas canónicas declaradas en la especificación OpenAPI
- **THEN** las rutas de recursos utilizan exclusivamente sustantivos (Regla Dura #8), y cualquier ruta histórica con verbos se encuentra marcada como deprecada.

#### Scenario: Partial updates strictly restricted to PATCH method
- **WHEN** se analizan las operaciones de actualización parcial de recursos (como estado de turnos o contraseñas)
- **THEN** se utiliza exclusivamente el método HTTP PATCH (Regla Dura #9), sin exponer endpoints de mutación parcial con PUT.

### Requirement: Continuous Integration Pipeline Automation
El repositorio SHALL contar con un pipeline de Integración Continua en GitHub Actions que valide automáticamente la integridad del backend, el frontend y la infraestructura en cada push o pull request a la rama principal.

#### Scenario: Automated multi-job pipeline verification on pull request
- **WHEN** se emite un push o pull request hacia la rama main
- **THEN** el pipeline ejecuta jobs paralelos para ejecutar la suite completa de pruebas de backend con pytest en Python 3.12.

#### Scenario: Complete test and build verification in CI frontend job
- **WHEN** el job de frontend se ejecuta en el pipeline de CI
- **THEN** ejecuta la suite de pruebas con `npm test`, valida el tipado estricto de TypeScript (`tsc --noEmit`) y compila exitosamente los assets con Vite.

#### Scenario: Docker composition validation in CI
- **WHEN** el job de infraestructura valida los contenedores
- **THEN** verifica que las configuraciones de `docker-compose.yml` y `docker-compose.prod.yml` sean válidas mediante `docker compose config`.
