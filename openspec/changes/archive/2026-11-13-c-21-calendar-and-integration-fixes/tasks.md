# Tasks: C-21 Calendario de Confirmados e Integración Fullstack

- [x] 1.1 Crear endpoint `GET /api/odontologos` en `backend/app/api/odontologos.py` con schema `extra="forbid"` y montarlo en `backend/app/main.py`.
- [x] 1.2 Agregar tests de integración en `backend/tests/test_odontologos.py` sin mocks de DB (Regla Dura #7).
- [x] 1.3 Actualizar `seed.py` para reiniciar secuencias en PostgreSQL (`RESTART IDENTITY`) cuando `reset=True`.
- [x] 2.1 Integrar `getOdontologos()` y `useOdontologosQuery()` en `PacienteDisponibilidadPage.tsx` con selección por defecto dinámica y modal de confirmación.
- [x] 2.2 Agregar ruta `/odontologo/calendario` y enlace `Calendario` en el header de `AppLayout.tsx`, sincronizando la vista mensual de turnos confirmados en `OdontologoAgendaPage.tsx`.
- [x] 2.3 Alinear `DEMO_ACCOUNTS` en `LoginPage.tsx` y la tabla de credenciales en `README.md` con los datos de `seed.py`.
- [x] 3.1 Crear `frontend/.dockerignore` y `backend/.dockerignore` y validar compilación limpia con `docker compose -f docker-compose.prod.yml build`.
- [x] 3.2 Ejecutar suites `pytest` y `vitest` verificando cumplimiento de las 13 Reglas Duras.
