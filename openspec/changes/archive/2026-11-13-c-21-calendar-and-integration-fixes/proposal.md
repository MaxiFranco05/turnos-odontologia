# C-21: Calendario de Confirmados para Odontólogo y Fixes de Integración

## Why

Durante la validación integral previa al despliegue y demostración en vivo sobre PostgreSQL y Docker Compose, se detectaron cuatro desajustes operativos y de experiencia de usuario que impedían una operación fluida entre los tres portales:
1. El selector de profesionales en `PacienteDisponibilidadPage` utilizaba IDs fijos (`2`, `3`, `5`), provocando errores HTTP `422` ("El usuario especificado no posee el rol de odontólogo") cuando las secuencias de PostgreSQL diferían.
2. El portal de Odontólogo solo contaba con la vista diaria (`Mi agenda`), sin un acceso dedicado en el header para consultar en un calendario mensual los turnos confirmados por Recepción.
3. Los accesos rápidos de `LoginPage` y la tabla de credenciales en `README.md` estaban desalineados respecto a los usuarios sembrados por `seed.py` (C-16), y `seed.py --reset` en PostgreSQL no reiniciaba las secuencias autoincrementales.
4. Los contextos de Docker de `frontend/` y `backend/` carecían de `.dockerignore`, lo que provocaba la copia de `node_modules` de Windows dentro de la imagen Alpine (`node.exe: not found`).

## What Changes

- **Backend**:
  - Nuevo endpoint REST `GET /api/odontologos` (`backend/app/api/odontologos.py`) con schema Pydantic `OdontologoPublicResponse(extra="forbid")` y consulta SQLAlchemy 2.0 `select()` filtrando `rol == RolUsuario.ODONTOLOGO`.
  - Actualización de `seed.py` para ejecutar `TRUNCATE ... RESTART IDENTITY CASCADE` en PostgreSQL cuando `reset=True`, preservando `delete()` en SQLite para tests.
- **Frontend**:
  - Consumo dinámico de `GET /api/odontologos` en `PacienteDisponibilidadPage.tsx`, con tarjeta de profesional seleccionado y modal de confirmación detallado.
  - Nueva ruta `/odontologo/calendario` y enlace `Calendario` en la cápsula del header de `AppLayout.tsx`, renderizando el calendario mensual interactivo de turnos confirmados por Recepción en `OdontologoAgendaPage.tsx`.
  - Alineación de `DEMO_ACCOUNTS` en `LoginPage.tsx` y `README.md` con `seed.py`.
- **Infraestructura Docker**:
  - Creación de `frontend/.dockerignore` y `backend/.dockerignore` para builds reproducibles y livianos.

## Capabilities

### New Capabilities
- `odontologos-catalog`: Endpoint público de solo lectura `GET /api/odontologos` para listar odontólogos activos con su matrícula y especialidad sin exponer credenciales.
- `odontologo-calendario`: Vista mensual interactiva en `/odontologo/calendario` accesible desde el header del portal de Odontólogo para consultar y registrar asistencia sobre turnos confirmados por Recepción.

### Modified Capabilities
- `patient-portal-ui`: Selector dinámico de odontólogos conectado a la base real y modal de confirmación con datos del profesional.
- `docker-prod-build`: Exclusión de artefactos locales (`node_modules`, `dist`, `__pycache__`) mediante `.dockerignore`.
- `seed-data-reset`: Reinicio de secuencias `RESTART IDENTITY` en PostgreSQL al ejecutar `seed.py --reset`.

## Impact

- **Backend**: `backend/app/api/odontologos.py`, `backend/app/main.py`, `backend/app/infrastructure/seed.py`, `backend/tests/test_odontologos.py`.
- **Frontend**: `frontend/src/layouts/AppLayout.tsx`, `frontend/src/router/routes.tsx`, `frontend/src/pages/OdontologoAgendaPage.tsx`, `frontend/src/pages/PacienteDisponibilidadPage.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/hooks/usePatientPortal.ts`, `frontend/src/services/patient.service.ts`.
- **Infraestructura / Docs**: `frontend/.dockerignore`, `backend/.dockerignore`, `README.md`.
