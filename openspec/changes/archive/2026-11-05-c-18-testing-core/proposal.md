# Proposal

## Why

El proyecto `turnos-odontologia` cuenta con una sólida base de pruebas unitarias de modelos, repositorios y routers (129 pruebas pasando), pero requiere consolidar su pirámide de pruebas con tests de integración de extremo a extremo (E2E) que recorran el ciclo de vida completo del turno entre múltiples actores concurrentes, validación automatizada de contratos OpenAPI para asegurar el cumplimiento de las directivas de arquitectura REST (Reglas Duras #8 y #9), y un pipeline de Integración Continua (CI) en GitHub Actions que garantice la calidad, tipado y construibilidad del sistema en cada pull request y push.

Este change introduce una suite E2E de ciclo de vida clínico multirol (incluyendo invariante anti-solape y ventana de anticipación), una suite de validación de contratos de API OpenAPI, y el workflow automatizado `.github/workflows/ci.yml`.

## What Changes

- **Suite de Pruebas de Integración E2E (`backend/tests/test_e2e_turnos_lifecycle.py`)**:
  - Flujo Principal E2E: Autenticación de paciente $\to$ consulta de disponibilidad $\to$ solicitud de turno (`solicitado`) $\to$ autenticación de recepción $\to$ consulta de agenda diaria $\to$ confirmación de turno (`confirmado`) $\to$ autenticación de odontólogo $\to$ consulta de turnos asignados $\to$ registro de asistencia (`presente`) $\to$ verificación de inmutabilidad ante cancelaciones tardías (409 Conflict).
  - Flujo Anti-solape Concurrente E2E (Regla Dura #13 y RN-AG-01): Intento de un segundo paciente de reservar el mismo slot horario y odontólogo de un turno vigente $\to$ rechazo inmediato con 409 Conflict.
  - Flujo de Cancelación Anticipada E2E: Solicitud de turno $\to$ cancelación anticipada con $>24$ h por paciente $\to$ verificación de liberación del hueco en `/api/disponibilidad`.
  - Flujo de Cancelación Tardía E2E (RN-TU-05): Intento de cancelación por paciente dentro de la ventana mínima de 24 h previa a la cita $\to$ rechazo con 422 Unprocessable Entity.
  - Flujo de Control de Acceso E2E: Odontólogo intentando marcar asistencia sobre turno ajeno $\to$ rechazo con 403 Forbidden.
  - Anonimización total: Uso estricto de datos sintéticos ficticios para todos los actores de prueba (Regla Dura #12).
- **Suite de Validación de Contratos OpenAPI (`backend/tests/test_openapi_contract.py`)**:
  - Verificación de esquema OpenAPI 3.x generado por FastAPI.
  - Verificación de la **Regla Dura #8**: NUNCA verbos en rutas HTTP (todas las URIs basadas en recursos sustantivos: `/api/turnos`, `/api/plantillas`, `/api/disponibilidad`, `/api/auth/login`, `/api/auth/password`).
  - Tratamiento de compatibilidad: Verificación de que rutas heredadas con verbos (como `/api/auth/cambiar-password`) estén marcadas explícitamente con `deprecated=True`.
  - Verificación de la **Regla Dura #9**: Actualizaciones parciales implementadas exclusivamente mediante método `PATCH` (no `PUT`).
  - Verificación del esquema de seguridad JWT Bearer en endpoints protegidos.
- **Pipeline de Integración Continua (`.github/workflows/ci.yml`)**:
  - Workflow automatizado en GitHub Actions ejecutado en ramas `main` y en `pull_request`.
  - Job `backend`: Checkout, setup de Python 3.12, caché de pip, instalación de dependencias y ejecución de la suite completa con `pytest`.
  - Job `frontend`: Checkout, setup de Node.js 20, caché de npm, instalación (`npm ci`), ejecución de pruebas unitarias (`npm test`), typechecking estricto (`tsc --noEmit`), y build estático de producción (`npm run build`).
  - Job `docker-validation`: Validación sintáctica de `Dockerfile` y verificación de `docker-compose.yml` y `docker-compose.prod.yml` mediante `docker compose config`.

## Capabilities

### New Capabilities
- `testing-core`: Infraestructura integral de pruebas de integración E2E, validación de contratos OpenAPI conforme a las Reglas Duras REST, y pipeline de CI para validación continua de calidad y compilación.

### Modified Capabilities
<!-- None: No se modifican requisitos funcionales de negocio existentes -->

## Impact

- **Tests Backend**: Se añaden `backend/tests/test_e2e_turnos_lifecycle.py` y `backend/tests/test_openapi_contract.py`.
- **CI/CD**: Se crea `.github/workflows/ci.yml`.
- **Código de Producción**: Marcado de deprecación formal en `/api/auth/cambiar-password` para promover `/api/auth/password`.
- **Riesgo**: Nulo para producción, eleva sustancialmente la detectabilidad de regresiones y fallos de contratos.
