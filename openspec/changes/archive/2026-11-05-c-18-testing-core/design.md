# Design

## Context

El proyecto `turnos-odontologia` cuenta con 129 pruebas unitarias y de integración por router en `backend/tests/`. No obstante, para garantizar la resiliencia en integración continua (CI) y certificar la calidad arquitectónica para el TP Integrador, es indispensable complementar la pirámide de pruebas con:
1. Pruebas E2E de ciclo de vida completo del turno entre múltiples actores (`paciente`, `recepcion`, `odontologo`), validando además la invariante anti-solape (Regla Dura #13) y la ventana de anticipación mínima (RN-TU-05).
2. Validación programática de contratos OpenAPI para auditar las **Reglas Duras #8** (NUNCA verbos en paths) y **#9** (NUNCA PUT para updates parciales), promoviendo `/api/auth/password` y depreciando formalmente `/api/auth/cambiar-password`.
3. Pipeline de CI en GitHub Actions que compile y pruebe backend, frontend (incluyendo `npm test`) y configuraciones de Docker.

## Goals / Non-Goals

**Goals:**
- Implementar `backend/tests/test_e2e_turnos_lifecycle.py` con flujos completos que simulen la interacción real de múltiples pacientes reservando en slots adyacentes o concurrentes (anti-solape 409), recepción confirmando, odontólogo registrando asistencia y validación de reglas de negocio cruzadas (cancelación tardía 422).
- Garantizar anonimización y uso de datos puramente sintéticos ficticios en los fixtures E2E (Regla Dura #12).
- Implementar `backend/tests/test_openapi_contract.py` inspeccionando `app.openapi()` para garantizar el cumplimiento de OpenAPI 3.x, URIs basadas puramente en sustantivos y métodos REST consistentes.
- Implementar `.github/workflows/ci.yml` con tres jobs independientes: `backend-tests`, `frontend-check` (con `npm test`, `tsc --noEmit` y `npm run build`) y `docker-lint`.
- Asegurar 100% de tests en verde sin degradar los 129 tests existentes (no-regresión).

**Non-Goals:**
- Despliegue continuo (CD) automático a nube o VPS en este change.
- Reemplazo de las pruebas unitarias existentes (este change complementa la pirámide en los niveles E2E, contratos y CI).

## Decisions

### 1. Test E2E de Ciclo de Vida Multirol con Clientes HTTP Aislados y Anti-solape
- **Decisión**: La suite `test_e2e_turnos_lifecycle.py` ejecutará solicitudes HTTP asíncronas encadenadas (`httpx.AsyncClient` sobre la app FastAPI), autenticando sucesivamente a cada actor:
  1. **Flujo Principal**: Paciente solicita turno en hueco derivado de plantilla $\to$ recepción lista agenda del día y transiciona a `confirmado` $\to$ odontólogo asignado lista sus turnos y marca `presente` $\to$ paciente intenta cancelar el turno ya atendido y recibe `409 Conflict`.
  2. **Invariante Anti-solape (Regla Dura #13)**: Un segundo paciente (`paciente_2`) intenta solicitar el mismo hueco horario ya tomado por `paciente_1` $\to$ la API rechaza transaccionalmente con `409 Conflict`.
  3. **Ventana de Anticipación (RN-TU-05)**: Paciente intentando cancelar con $<24$ h recibe `422 Unprocessable Entity`; paciente cancelando con $>24$ h libera el slot en `/api/disponibilidad`.
  4. **RBAC Cruzado**: Odontólogo intentando marcar asistencia de un turno de otro colega recibe `403 Forbidden`.
- **Razón**: Valida la interacción multicapa real (autenticación JWT, verificación de roles, máquina de estados transaccional y persistencia) en un solo flujo cohesionado.

### 2. Validador Automatizado de Contratos OpenAPI (Reglas Duras #8 y #9)
- **Decisión**: `test_openapi_contract.py` extraerá la especificación `app.openapi()` y aplicará aserciones sobre todas las rutas y métodos:
  - Rutas canónicas basadas en sustantivos: `/api/turnos`, `/api/plantillas`, `/api/disponibilidad`, `/api/auth/login`, `/api/auth/password`.
  - Deprecación de rutas históricas: La ruta `/api/auth/cambiar-password` se valida como `deprecated: true` en el esquema OpenAPI de FastAPI.
  - Lista de bloqueo de verbos: Ningún segmento de ruta canónica no deprecada puede coincidir con verbos comunes (`crear`, `borrar`, `actualizar`, `cancelar`, `confirmar`, `solicitar`, `get`, `post`, `put`, `delete`).
  - Restricción de mutación parcial: Ningún endpoint de actualización parcial expone método `PUT`; todas las modificaciones de estado se realizan con `PATCH`.
  - Esquema de seguridad: Existencia de `HTTPBearer` en `components.securitySchemes`.
- **Razón**: Convierte las reglas de diseño REST en aserciones de código inquebrantables que fallan automáticamente si un desarrollador introduce un endpoint no REST.

### 3. Pipeline de GitHub Actions (`ci.yml`) Modular y Rápido
- **Decisión**: Estructurar `.github/workflows/ci.yml` con tres jobs que corren en `ubuntu-latest`:
  - `backend`: Setup Python 3.12, caché `pip`, `pip install -r backend/requirements.txt`, y ejecución de `pytest backend/tests`.
  - `frontend`: Setup Node.js 20, caché `npm`, `npm ci` en `frontend/`, ejecución de tests con `npm test -- --run`, typecheck con `tsc --noEmit`, y compilación de producción con `npm run build`.
  - `docker-validation`: `docker compose -f docker-compose.yml config` y `docker compose -f docker-compose.prod.yml config`.
- **Razón**: Garantiza la verificación completa en CI sin saltarse las pruebas de frontend ni de infraestructura.

## Risks / Trade-offs

- **[Riesgo: Tiempos de ejecución prolongados en CI]** → **Mitigación**: Uso de acciones nativas `actions/cache` y `actions/setup-python` / `actions/setup-node` con soporte de caché integrado.
- **[Riesgo: Fragilidad por orden de ejecución en tests E2E]** → **Mitigación**: Cada test E2E es atómico y autocontenido; genera sus propios usuarios y plantillas dentro de una transacción aislada de prueba.

## Migration Plan

1. Actualizar `/api/auth/cambiar-password` en `backend/app/api/auth.py` para marcarlo como `deprecated=True`.
2. Crear `backend/tests/test_e2e_turnos_lifecycle.py` bajo Strict TDD.
3. Crear `backend/tests/test_openapi_contract.py` bajo Strict TDD.
4. Crear `.github/workflows/ci.yml`.
5. Ejecutar toda la batería de pruebas y verificar 100% de suites en verde.
