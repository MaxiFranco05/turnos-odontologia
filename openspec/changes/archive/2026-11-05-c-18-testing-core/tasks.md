# Tasks

## 1. Tests de Integración E2E de Ciclo de Vida Clínico

- [x] 1.1 Implementar `backend/tests/test_e2e_turnos_lifecycle.py` con el flujo principal E2E (login paciente -> solicitar turno en hueco disponible -> login recepción -> confirmar turno en agenda diaria -> login odontólogo -> registrar asistencia como presente -> verificación de inmutabilidad ante cancelaciones posteriores con 409 Conflict), utilizando datos puramente sintéticos y ficticios conforme a la Regla Dura #12.
- [x] 1.2 Agregar escenarios E2E para la invariante anti-solape (intento de reserva de segundo paciente rechazado con 409 Conflict, Regla Dura #13), cancelación anticipada (>24 h con verificación de liberación inmediata del hueco en `/api/disponibilidad`), caso negativo de cancelación tardía (<24 h rechazada con 422 Unprocessable Entity), y rechazo con código 403 Forbidden cuando un odontólogo intenta marcar asistencia sobre el turno de otro colega.

## 2. Validación de Contratos OpenAPI y Reglas Duras REST

- [x] 2.1 Marcar el endpoint histórico `/api/auth/cambiar-password` con `deprecated=True` en `backend/app/api/auth.py` para promover formalmente la ruta canónica basada en sustantivos `/api/auth/password`.
- [x] 2.2 Implementar `backend/tests/test_openapi_contract.py` validando la generación de especificación OpenAPI 3.x, componentes de seguridad Bearer JWT, cumplimiento estricto de la Regla Dura #8 (rutas canónicas sustantivas sin verbos y deprecación de alias históricos) y cumplimiento de la Regla Dura #9 (NUNCA PUT para updates parciales, uso exclusivo de HTTP PATCH en modificaciones de estado y atributos clínicos).

## 3. Pipeline de Integración Continua (CI) y Verificación de Regresión

- [x] 3.1 Crear `.github/workflows/ci.yml` configurando jobs paralelos en GitHub Actions para backend (Python 3.12 con pytest), frontend (Node 20 con `npm test -- --run`, `tsc --noEmit` y `npm run build`), y validación de sintaxis de Docker Compose (`docker-compose.yml` y `docker-compose.prod.yml`).
- [x] 3.2 Ejecutar la suite completa de pruebas de backend con pytest verificando que los nuevos tests E2E y de contratos se ejecuten satisfactoriamente y el 100% de las pruebas del proyecto permanezcan en verde.
