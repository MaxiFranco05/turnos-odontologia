# Design

## Context

El sistema cuenta con un archivo `docker-compose.yml` para desarrollo local y un `backend/Dockerfile` multi-stage optimizado para FastAPI. Sin embargo, no existe configuración de despliegue para el frontend (actualmente ejecutado con `npm run dev` en la máquina anfitriona) ni una composición que ensamble la arquitectura completa bajo premisas de producción (seguridad, aislamiento de base de datos, reverse proxy unificado, límites de CPU/RAM y verificación de salud continua). Ver motivación completa en `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Proveer `docker-compose.prod.yml` que orqueste `postgres`, `api` y `frontend` en un entorno autocontenido de producción.
- Crear un `Dockerfile` multi-stage para `frontend` que compile la SPA con Vite y la sirva a través de un servidor web Nginx de alto rendimiento y bajo consumo.
- Configurar Nginx para actuar como reverse proxy transparente hacia `api` (`/api/` y `/health/`), garantizando soporte SPA (`try_files $uri $uri/ /index.html;`) y compresión gzip.
- Cumplir de manera irrestricta con la **Regla Dura #10**: healthchecks y límites de recursos (`cpus` y `memory`) en **todos** los servicios.
- Aislar el puerto de PostgreSQL (`5432`), asegurando que no se exponga al host ni a internet, restringiendo el tráfico a la red interna de contenedores.
- Entregar una plantilla de variables de entorno `.env.prod.example` documentada y libre de secretos reales (Reglas Duras #11 y #12).
- Añadir tests automatizados en `backend/tests/test_docker_prod_config.py` para asegurar que las configuraciones de producción respeten la sintaxis y las directivas de seguridad.

**Non-Goals:**
- Generación automática de certificados SSL/TLS con Let's Encrypt o certbot en v1 (el contenedor Nginx publica en el puerto 80, preparado para operar detrás de un Ingress, CDN o terminador TLS externo como Cloudflare/Traefik).
- Automatización de pipelines CI/CD o manifiestos Kubernetes.
- Servidor de tareas asíncronas Redis (previsto para v2+ según `knowledge-base/08_arquitectura_propuesta.md`).

## Decisions

### 1. Servidor web estático y proxy reverso con Nginx Alpine
- **Decisión**: Utilizar `nginx:1.27-alpine` como runtime del frontend para servir los assets estáticos generados por Vite y enrutar las solicitudes de API.
- **Razón**: Nginx consume menos de 15 MB de RAM, maneja compresión gzip de forma nativa, ofrece alto throughput para archivos estáticos y simplifica la topología al unificar frontend y backend bajo un único puerto HTTP (80).
- **Alternativas consideradas**:
  - Servir frontend con Node `vite preview` o `serve`: Descartado por alto consumo de memoria (>100MB), vulnerabilidad a DoS y falta de optimización para producción.
  - Caddy / Traefik: Descartado para mantener consistencia con el stack estándar de cátedra y minimizar dependencias no estándar.

### 2. Multi-stage Dockerfile para Frontend
- **Decisión**: Implementar `frontend/Dockerfile` en dos etapas:
  - `builder`: Basado en `node:20-alpine` (o 22-alpine), copia `package*.json`, instala dependencias (`npm ci` o `npm install`), copia el código y ejecuta `npm run build`.
  - `runner`: Basado en `nginx:1.27-alpine`, copia únicamente el directorio `dist` compilado hacia `/usr/share/nginx/html` y reemplaza la configuración de Nginx por `nginx.conf`.
- **Razón**: La imagen final pesa menos de 30 MB (frente a >600 MB con Node y devDependencies), elimina herramientas de desarrollo del contenedor final y reduce la superficie de vulnerabilidades.

### 3. Aislamiento de red y no exposición del puerto de PostgreSQL
- **Decisión**: Los tres servicios comparten una red interna tipo puente (`app_network`). El servicio `postgres` omite la sección `ports`, de modo que el puerto 5432 es accesible únicamente por el contenedor `api` mediante resolución DNS interna `postgres:5432`. El servicio `api` tampoco publica su puerto al host, siendo accesible únicamente a través del reverse proxy `frontend` (Nginx). Solo el contenedor `frontend` expone el puerto `80:80`.
- **Razón**: Previene escaneos y ataques directos de fuerza bruta contra PostgreSQL y la API desde redes externas.

### 4. Implementación estricta de Healthchecks (Regla Dura #10)
- **Decisión**: Configurar directivas `healthcheck` en cada servicio de `docker-compose.prod.yml`:
  - `postgres`: `test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-turnos_odontologia}"]`, con intervalo 10s, timeout 5s, 5 reintentos, start_period 10s.
  - `api`: `test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')\""]`, con intervalo 15s, timeout 5s, 3 reintentos, start_period 15s. Utiliza la librería estándar de Python para evitar depender de `curl`.
  - `frontend`: `test: ["CMD-SHELL", "wget -q --spider http://localhost:80/healthz || exit 1"]`, con intervalo 15s, timeout 5s, 3 reintentos, start_period 5s. Utiliza `wget` nativo de Alpine/busybox.
- **Razón**: Permite la orquestación con `depends_on: { service: healthy }` y garantiza que contenedores degradados o congelados sean detectados y reiniciados inmediatamente.

### 5. Asignación de límites y reservas de recursos
- **Decisión**: Cada servicio en `docker-compose.prod.yml` define `deploy.resources.limits` y `reservations`:
  - `postgres`: límite `cpus: "1.0"`, `memory: 512M`; reserva `memory: 128M`.
  - `api`: límite `cpus: "1.0"`, `memory: 512M`; reserva `memory: 128M`.
  - `frontend`: límite `cpus: "0.5"`, `memory: 128M`; reserva `memory: 32M`.
- **Razón**: Evita agotamiento de memoria (OOM killer global) en el host y garantiza estabilidad bajo carga concurrente.

### 6. Configuración de Nginx (`nginx.conf`)
- **Decisión**: Proveer un archivo de configuración que:
  - Exponga `/healthz` con respuesta directa `200 "OK"` sin escribir en disco.
  - Aplique `try_files $uri $uri/ /index.html;` para soportar navegación del lado del cliente en React Router sin errores 404 al recargar páginas.
  - Redirija peticiones `/api/` hacia `http://api:8000/api/` y `/health/` hacia `http://api:8000/health/` con encabezados `Host`, `X-Real-IP`, `X-Forwarded-For` y `X-Forwarded-Proto`.
  - Habilite cabeceras de seguridad (`X-Frame-Options SAMEORIGIN`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`).

## Risks / Trade-offs

- **[Riesgo: 404 al refrescar URLs profundas en el navegador]** → **Mitigación**: Directiva `try_files $uri $uri/ /index.html;` configurada en el bloque `location /` de Nginx.
- **[Riesgo: Bloqueo de inicio si la base de datos tarda en aceptar conexiones]** → **Mitigación**: `api` declara `depends_on: postgres: condition: service_healthy` junto con el healthcheck de `pg_isready`.
- **[Riesgo: Exposición accidental de credenciales en repositorios]** → **Mitigación**: `.env.prod.example` utiliza valores puramente sintéticos y `${VAR}` de sustitución; `.env.prod` permanece listado en `.gitignore`.
- **[Riesgo: Incompatibilidad de curl en imágenes mínimas]** → **Mitigación**: Usar `python -c urllib` en el backend y `wget` en Nginx Alpine; ambas son herramientas nativas de sus respectivas imágenes base.

## Migration Plan

1. Crear `frontend/nginx.conf` con las reglas de proxy, fallback y healthcheck.
2. Crear `frontend/Dockerfile` multi-stage con build de Vite y runner Nginx.
3. Crear `.env.prod.example` con la especificación de variables de producción.
4. Crear `docker-compose.prod.yml` ensamblando los tres contenedores con sus healthchecks, límites y volúmenes.
5. Desarrollar suite de pruebas automatizadas `backend/tests/test_docker_prod_config.py` validando la estructura de archivos, directivas de salud y políticas de red.
6. En producción, desplegar mediante `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`.
