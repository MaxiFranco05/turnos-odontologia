# Proposal

## Why

El proyecto `turnos-odontologia` cuenta con un entorno de desarrollo funcional (`docker-compose.yml` y `backend/Dockerfile`), pero carece de una topología de orquestación contenerizada orientada a producción. Desplegar con la configuración de desarrollo expone riesgos críticos de seguridad y estabilidad: el puerto de PostgreSQL (5432) queda expuesto al host, el frontend se ejecuta en servidor de desarrollo Vite sin optimización estática ni reverse proxy unificado, y se carece de estandarización de límites de recursos y variables de entorno segregadas.

Esta propuesta introduce `docker-compose.prod.yml`, un `Dockerfile` multi-stage para `frontend` con Nginx como servidor estático y reverse proxy, un archivo de configuración de Nginx optimizado y seguro, y una plantilla de variables de entorno `.env.prod.example`, cumpliendo estrictamente con la Regla Dura #10 (healthchecks y límites de recursos en todos los servicios) y los estándares de seguridad de la arquitectura del proyecto.

## What Changes

- **Nuevo `docker-compose.prod.yml`**: Topología contenerizada de producción compuesta por tres servicios interconectados mediante redes internas aisladas:
  - `postgres`: PostgreSQL 16 Alpine con almacenamiento persistente en volumen nombrado, sin puertos expuestos al host, límites de CPU/memoria y healthcheck con `pg_isready`.
  - `api`: Backend FastAPI compilado en multi-stage, ejecutado como usuario no privilegiado (`appuser`), con healthcheck en `/health/ready` y límites de CPU/memoria.
  - `frontend`: Frontend React SPA compilado a assets estáticos y servido por Nginx con reverse proxy hacia la API (`/api/` y `/health/`), healthcheck en `/healthz`, límites de CPU/memoria y publicación controlada en el puerto 80 del host.
- **Nuevo `frontend/Dockerfile`**: Dockerfile multi-stage con etapa de construcción en Node Alpine (`npm run build`) y etapa de ejecución ligera en Nginx Alpine, ejecutando con usuario no privilegiado y directiva `HEALTHCHECK`.
- **Nuevo `frontend/nginx.conf`**: Configuración de servidor web con compresión gzip, cabeceras de seguridad HTTP, soporte de navegación SPA (`try_files $uri $uri/ /index.html;`), proxy reverso transparente a `http://api:8000` y endpoint de salud `/healthz`.
- **Nueva plantilla `.env.prod.example`**: Archivo de referencia documentando las variables obligatorias en producción (`DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `JWT_SECRET`, etc.) sin credenciales reales (Regla Dura #12).
- **Nueva suite de validación automatizada `backend/tests/test_docker_prod_config.py`**: Pruebas unitarias de infraestructura que parsean y validan la sintaxis YAML de `docker-compose.prod.yml`, la presencia de healthchecks y límites de recursos en cada servicio (Regla Dura #10), y la ausencia de exposición pública del puerto de base de datos.

## Capabilities

### New Capabilities
- `docker-compose-prod`: Orquestación y empaquetado para despliegue productivo de la clínica odontológica, incluyendo composición de servicios, multi-stage builds, reverse proxy Nginx con fallback SPA, aislamiento de red, healthchecks y límites de recursos por contenedor.

### Modified Capabilities
<!-- None: Las capacidades funcionales existentes del sistema no sufren modificaciones de comportamiento -->

## Impact

- **Infraestructura**: Se agregan `docker-compose.prod.yml`, `frontend/Dockerfile`, `frontend/nginx.conf` y `.env.prod.example`.
- **Backend**: Se agrega `backend/tests/test_docker_prod_config.py` para asegurar que las configuraciones de producción no se degraden en futuros cambios.
- **Seguridad**: Se elimina la superficie de ataque sobre la base de datos al no publicar el puerto 5432 al exterior; Nginx actúa como fachada unificada y añade cabeceras defensivas (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).
- **Compatibilidad**: No altera los flujos de desarrollo existentes (`docker-compose.yml` sigue disponible e inalterado).
