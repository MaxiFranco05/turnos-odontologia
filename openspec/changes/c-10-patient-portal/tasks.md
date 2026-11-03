# Tasks: C-10 (`c-10-patient-portal`) — Portal del Paciente (`GET /api/mis-turnos`)

> **Strict TDD Mode: enabled**
> Cada tarea DEBE ejecutarse bajo el ciclo **RED → GREEN → TRIANGULATE → REFACTOR**, registrando la tabla `TDD Cycle Evidence`.
> **Tests sin mocks de base de datos (Regla Dura #7)**: usar la base de datos SQLite en memoria real (`backend/tests/test_patient_portal.py`) y datos sintéticos ficticios (**Regla Dura #12**).

---

## 1. Capa de Dominio, Aplicación e Infraestructura (Bordes de Rango de Fechas y Prevención N+1)

- [x] **1.1** Implementar el helper puro sincrónico `def get_clinic_date_range_bounds(fecha_desde: datetime.date | None = None, fecha_hasta: datetime.date | None = None, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` en `backend/app/application/turnos.py` (**Regla Dura #3**: `def` sincrónico puro, sin `async def` ni llamadas al reloj del sistema) y encadenar `.options(selectinload(Turno.odontologo))` en `SqlAlchemyTurnoRepository.find_by_patient_range` (`backend/app/infrastructure/repositories/turno.py`, **Regla Dura #2**).
  - **Criterios de aceptación**:
    - Si `fecha_desde` y `fecha_hasta` están presentes y `fecha_hasta < fecha_desde`, lanza `ValueError` con mensaje descriptivo.
    - Si `fecha_desde` está presente, `start` es `00:00:00` en `ZoneInfo(timezone_str or DEFAULT_CLINIC_TIMEZONE)` (`America/Argentina/Buenos_Aires`); si se omite, `start` usa `datetime.date(1970, 1, 1)` a las `00:00:00` en la misma zona horaria.
    - Si `fecha_hasta` está presente, `end` es `(fecha_hasta + timedelta(days=1))` a las `00:00:00` en la misma zona horaria; si se omite, `end` usa `datetime.date(2100, 1, 1) + timedelta(days=1)` a las `00:00:00` en la misma zona horaria.
    - `SqlAlchemyTurnoRepository.find_by_patient_range` ejecuta `select(Turno).options(selectinload(Turno.odontologo)).where(Turno.paciente_id == paciente_id, Turno.inicio < end, Turno.fin > start).order_by(Turno.inicio)` para eliminar cualquier riesgo de consulta N+1 al serializar `OdontologoResumenResponse`.
  - **Tests TDD (`backend/tests/test_patient_portal.py`)**:
    - Tests unitarios para `get_clinic_date_range_bounds` (sin filtros, solo `fecha_desde`, solo `fecha_hasta`, rango válido `fecha_desde <= fecha_hasta`, y rango invertido `fecha_hasta < fecha_desde` lanzando `ValueError`).
    - Test de repositorio verificando que `find_by_patient_range` precarga `Turno.odontologo` sin lazy-load adicional.

---

## 2. Capa de Presentación HTTP (`GET /api/mis-turnos` para `RolUsuario.PACIENTE` + Seguridad OWASP BOLA/BOPLA)

- [x] **2.1** Definir `OdontologoResumenResponse` y `MisTurnosPacienteItemResponse` con `ConfigDict(extra="forbid", from_attributes=True)` (**Regla Dura #1**, prevención OWASP API3:2023 BOPLA) y extender `GET /api/mis-turnos` en `backend/app/api/mis_turnos.py` para soportar `RolUsuario.PACIENTE` junto con `RolUsuario.ODONTOLOGO`.
  - **Criterios de aceptación**:
    - `OdontologoResumenResponse` expone únicamente `id: int`, `nombre: str`, `nro_socio: str | None`, `email: str | None` (excluyendo `password_hash`, `rol`, `debe_cambiar_password`, `perfil_completo`).
    - `MisTurnosPacienteItemResponse` expone `id`, `paciente_id`, `odontologo_id`, `inicio`, `fin`, `motivo`, `estado`, `origen`, `odontologo: OdontologoResumenResponse`.
    - `GET /api/mis-turnos` autoriza `Depends(require_roles(RolUsuario.ODONTOLOGO, RolUsuario.PACIENTE))` (retornando `403 Forbidden` para `RolUsuario.RECEPCION`, `401 Unauthorized` sin JWT válido, y `403 password_change_required` si `debe_cambiar_password=True`).
    - Para `current_user.rol == RolUsuario.ODONTOLOGO`: requiere `fecha: datetime.date` y rechaza `fecha_desde` / `fecha_hasta` con `422 Unprocessable Entity`; invoca `repo.find_by_dentist_range(odontologo_id=current_user.id, ...)`.
    - Para `current_user.rol == RolUsuario.PACIENTE`: rechaza `fecha` con `422 Unprocessable Entity`, acepta `fecha_desde` y `fecha_hasta` opcionales (`422 Unprocessable Entity` si `fecha_hasta < fecha_desde`), e invoca `repo.find_by_patient_range(paciente_id=current_user.id, start=range_start, end=range_end)` (prevención inquebrantable de OWASP API1:2023 BOLA/IDOR).
  - **Tests TDD (`backend/tests/test_patient_portal.py` y actualización de `backend/tests/test_dentist_agenda.py`)**:
    - Listado completo de turnos propios del paciente (futuros y pasados en estados `solicitado`, `confirmado`, `cancelado`, `anulado`, `presente`, `ausente`) ordenados por `inicio` ascendente con `odontologo` anidado y sin campos sensibles (`password_hash`).
    - Aislamiento BOLA/IDOR: Paciente A (`Lucía Gómez (Ficticia)`) NUNCA ve turnos de Paciente B (`Martín Pérez (Ficticio)`) aunque se intente inyectar `?paciente_id=...` en la query string.
    - Filtrado por rango inclusivo `fecha_desde` y `fecha_hasta` en `America/Argentina/Buenos_Aires`, y rechazo `422` cuando `fecha_hasta < fecha_desde` o cuando un paciente envía `?fecha=...` (o un odontólogo omite `fecha` / envía `fecha_desde`).
    - RBAC y seguridad: `403 Forbidden` para `recepcion`, `403 password_change_required` cuando `debe_cambiar_password=True`, `401 Unauthorized` sin token, y validación de `extra="forbid"` en `OdontologoResumenResponse` y `MisTurnosPacienteItemResponse`.
    - Flujo E2E US-004: Paciente consulta `GET /api/mis-turnos` y cancela un turno propio futuro (`>= 24h`) vía `PATCH /api/turnos/{id}` (`{"estado": "cancelado"}`), verificando que `GET /api/mis-turnos` refleja `estado="cancelado"`, que `GET /api/disponibilidad` libera el hueco (`CB-03`), y que con `< 24h` recibe `422 Unprocessable Entity` (`RN-TU-05`).
