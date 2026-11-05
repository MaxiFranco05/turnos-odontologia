# Tasks

## 1. Configuración de Servidor Web y Contenedor Frontend

- [x] 1.1 Crear `frontend/nginx.conf` con directiva `try_files` para SPA fallback, proxy reverso hacia `http://api:8000/api/` y `http://api:8000/health/`, cabeceras de seguridad y endpoint `/healthz` con respuesta HTTP 200.
- [x] 1.2 Crear `frontend/Dockerfile` multi-stage (etapa 1 builder en Node 20 Alpine con `npm run build`, etapa 2 runner en Nginx 1.27 Alpine) con directiva `HEALTHCHECK` integrada (Regla Dura #10) y validar la sintaxis de construcción.

## 2. Composición Productiva y Entorno Segregado

- [x] 2.1 Crear `.env.prod.example` definiendo todas las variables de entorno de producción requeridas (`APP_ENV=production`, `DATABASE_URL`, `JWT_SECRET`, etc.) utilizando exclusivamente datos sintéticos sin secretos reales (Reglas Duras #11 y #12).
- [x] 2.2 Crear `docker-compose.prod.yml` integrando `postgres`, `api` y `frontend` con red interna `app_network`, aislamiento total del puerto de PostgreSQL, healthchecks en cada servicio y directivas de límites/reservas de recursos (`deploy.resources.limits`) cumpliendo la Regla Dura #10.

## 3. Pruebas Automatizadas de Infraestructura y Verificación Integral

- [x] 3.1 Implementar suite de pruebas automatizadas en `backend/tests/test_docker_prod_config.py` bajo Strict TDD, validando el parseo sintáctico de `docker-compose.prod.yml`, la presencia de healthchecks en los tres servicios, los límites cuantitativos de CPU y memoria, y la ausencia de mapeos de puertos públicos en la base de datos.
- [x] 3.2 Ejecutar la suite completa de pruebas del backend verificando que la nueva batería de infraestructura pase limpiamente y que la regresión general se mantenga 100% en verde.
