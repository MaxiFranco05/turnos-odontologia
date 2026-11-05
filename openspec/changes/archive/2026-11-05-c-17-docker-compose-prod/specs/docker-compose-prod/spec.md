# Spec Delta

## Purpose

Provee la especificación de infraestructura contenerizada de producción para el sistema de turnos odontológicos, garantizando aislamiento de red, servidor web inverso con fallback SPA, límites de recursos y verificación continua de salud bajo la Regla Dura #10.

## ADDED Requirements

### Requirement: Production Compose Services and Network Isolation
El archivo de composición productiva SHALL orquestar los servicios `postgres`, `api` y `frontend` interconectados por una red puente interna, asegurando que la base de datos PostgreSQL no publique puertos directamente al host y solo sea accesible por el servicio de backend.

#### Scenario: Database is isolated without host port binding
- **WHEN** se inspecciona la definición del servicio `postgres` en la composición de producción
- **THEN** no debe contener mapeo de puertos (`ports`) hacia el host, restringiendo su conectividad exclusivamente a la red interna compartida con `api`.

#### Scenario: Healthcheck defined for all production services
- **WHEN** se analiza la especificación de cada servicio (`postgres`, `api`, `frontend`)
- **THEN** cada uno SHALL declarar una directiva `healthcheck` con comando de test, intervalo, timeout, reintentos y periodo de inicio (Regla Dura #10).

### Requirement: Resource Limits and Restart Policies
Cada contenedor definido en la composición de producción SHALL establecer límites estrictos de consumo de CPU y memoria (`deploy.resources.limits`), así como una política de reinicio persistente ante caídas inesperadas (`restart: unless-stopped` o `always`).

#### Scenario: Strict resource limits configured per service
- **WHEN** se valida la sección `deploy.resources.limits` de los servicios
- **THEN** todos los servicios deben tener definidos topes cuantitativos de `cpus` y `memory` para prevenir la degradación por inanición del host.

#### Scenario: Container auto-restart policy configured
- **WHEN** un contenedor se detiene por un reinicio del host o falla no fatal
- **THEN** el motor de contenedores SHALL reiniciar automáticamente el contenedor según la política configurada.

### Requirement: Multi-stage Frontend Production Container and Reverse Proxy
El contenedor de frontend SHALL compilar los assets estáticos de React/Vite en una etapa previa y servirlos mediante Nginx optimizado, redirigiendo rutas no encontradas a `/index.html` (SPA fallback) y proveyendo proxy reverso transparente a `/api/` y `/health/` del backend.

#### Scenario: Static bundle build and SPA fallback routing
- **WHEN** un cliente HTTP solicita una ruta de interfaz (ej. `/login`, `/agenda`, `/turnos`)
- **THEN** Nginx sirve el archivo correspondiente o resuelve en `/index.html` con código HTTP 200 para permitir el enrutamiento del lado del cliente.

#### Scenario: Unified API and health proxying via Nginx
- **WHEN** una petición con prefijo `/api/` o `/health/` ingresa al servidor Nginx
- **THEN** Nginx reenvía la solicitud al servicio de backend interno (`api:8000`) preservando encabezados de host y cliente, respondiendo al cliente con el resultado del backend.

#### Scenario: Nginx healthcheck endpoint availability
- **WHEN** se consulta el endpoint interno `/healthz` de Nginx
- **THEN** el servidor responde de forma inmediata con código HTTP 200 y cuerpo indicando estado operativo.

### Requirement: Production Environment Configuration Separation
La infraestructura SHALL separar la configuración de ejecución mediante una plantilla `.env.prod.example` con sintaxis válida, documentando todas las variables requeridas en producción sin incluir contraseñas reales ni datos sensibles de pacientes (Reglas Duras #11 y #12).

#### Scenario: Synthetic template provided without real secrets
- **WHEN** se audita el archivo `.env.prod.example`
- **THEN** contiene marcadores sintéticos o valores de ejemplo para `DATABASE_URL`, `POSTGRES_PASSWORD`, `JWT_SECRET` y variables de negocio, sin exponer secretos productivos reales en el repositorio.
