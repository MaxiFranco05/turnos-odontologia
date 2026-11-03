# Design: C-09 — Dentist Daily Agenda (`c-09-dentist-agenda`)

## Context

`C-02` (`core-models`) defined `Turno` with `lazy="selectin"` on both `Turno.paciente` and `Turno.odontologo` (`backend/app/domain/models/turno.py`), and `SqlAlchemyTurnoRepository.find_by_dentist_range(odontologo_id, start, end)` in `backend/app/infrastructure/repositories/turno.py` already queries `select(Turno).where(Turno.odontologo_id == odontologo_id, Turno.inicio < end, Turno.fin > start).order_by(Turno.inicio)`.

See `proposal.md` for motivation and scope, and `specs/dentist-agenda/spec.md` for normative requirements and scenarios.

## Goals / Non-Goals

**Goals:**
- Expose `GET /api/mis-turnos?fecha=YYYY-MM-DD` in a dedicated router `backend/app/api/mis_turnos.py` (registered in `backend/app/main.py`) prepared for seamless extension in `C-10` (`patient-portal`).
- Enforce strict server-side BOLA isolation (`odontologo_id = current_user.id` derived solely from the JWT token, never from query parameters) and RBAC (`require_roles(RolUsuario.ODONTOLOGO)` in `C-09`).
- Provide a pure synchronous function `def get_clinic_day_bounds(fecha: datetime.date, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py` (**Hard Rule #3**) to compute the half-open clinic day interval `[00:00:00, +1 day 00:00:00)` in `America/Argentina/Buenos_Aires`.
- Define strict Pydantic v2 response schemas `PacienteResumenResponse` and `MisTurnosOdontologoItemResponse` with `ConfigDict(extra="forbid", from_attributes=True)` (**Hard Rule #1**), exposing only non-sensitive patient identification fields (`id`, `nombre`, `nro_socio`, `email`).

**Non-Goals:**
- Patient range queries (`GET /api/mis-turnos?fecha_desde=&fecha_hasta=`) — scoped to `C-10` (`patient-portal`), which will extend `backend/app/api/mis_turnos.py`.
- Reception clinic-wide daily agenda (`GET /api/agenda/dia`) — scoped to `C-08` (`reception-agenda`).
- State transitions (`PATCH /api/turnos/{id}`) — already implemented and audited in `C-07`.

## Decisions

### 1. Dedicated Router `backend/app/api/mis_turnos.py` for `/api/mis-turnos`
- **Decision**: Create `backend/app/api/mis_turnos.py` with `router = APIRouter(prefix="/api/mis-turnos", tags=["mis-turnos"])` and include it in `backend/app/main.py`.
- **Rationale**: Both `C-09` (`dentist-agenda`) and `C-10` (`patient-portal`) share the resource path `/api/mis-turnos` in `CHANGES.md`. Placing `/api/mis-turnos` in its own router keeps `api/turnos.py` focused on `/api/turnos` (`POST` and `PATCH /{id}`) and allows `C-10` to extend `api/mis_turnos.py` cleanly without route collisions.

### 2. Pure Synchronous Clinic Day Window Calculation (`def get_clinic_day_bounds`)
- **Decision**: Implement `def get_clinic_day_bounds(fecha: datetime.date, timezone_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime]` in `backend/app/application/turnos.py`:
  ```python
  def get_clinic_day_bounds(
      fecha: datetime.date,
      timezone_str: str | None = None,
  ) -> tuple[datetime.datetime, datetime.datetime]:
      tz_name = timezone_str or DEFAULT_CLINIC_TIMEZONE
      zone = ZoneInfo(tz_name)
      day_start = datetime.datetime.combine(fecha, datetime.time.min, tzinfo=zone)
      day_end = day_start + datetime.timedelta(days=1)
      return day_start, day_end
  ```
- **Rationale**: Complies with **Hard Rule #3** (`def` synchronous for pure in-memory calculation without I/O) and reuses `SqlAlchemyTurnoRepository.find_by_dentist_range(odontologo_id=current_user.id, start=day_start, end=day_end)`, which already filters `Turno.inicio < day_end` and `Turno.fin > day_start` ordered by `Turno.inicio` ascending (**Hard Rule #2**).

### 3. Strict Response DTOs with Least-Privilege Patient Summary (OWASP API3:2023 — BOPLA)
- **Decision**: Define `PacienteResumenResponse` and `MisTurnosOdontologoItemResponse` in `backend/app/api/mis_turnos.py`:
  ```python
  class PacienteResumenResponse(BaseModel):
      model_config = ConfigDict(extra="forbid", from_attributes=True)

      id: int
      nombre: str
      nro_socio: str | None
      email: str | None


  class MisTurnosOdontologoItemResponse(BaseModel):
      model_config = ConfigDict(extra="forbid", from_attributes=True)

      id: int
      paciente_id: int
      odontologo_id: int
      inicio: datetime.datetime
      fin: datetime.datetime
      motivo: str
      estado: EstadoTurno
      origen: OrigenTurno
      paciente: PacienteResumenResponse
  ```
- **Rationale**: Prevents **OWASP API3:2023 (Broken Object Property Level Authorization / Excessive Data Exposure)** by explicitly projecting only the 4 identification fields the dentist needs (`id`, `nombre`, `nro_socio`, `email`) and never serializing `Usuario.password_hash`, `Usuario.debe_cambiar_password`, or `Usuario.rol`. Because `Turno.paciente` is configured with `lazy="selectin"` in `backend/app/domain/models/turno.py`, SQLAlchemy 2.0 loads the associated patients in a single batched `SELECT ... WHERE usuarios.id IN (...)` query without N+1 queries.

## Risks / Trade-offs

- **[Risk] Future `C-10` (`patient-portal`) sharing `GET /api/mis-turnos`** → **Mitigation**: Centralizing the endpoint in `backend/app/api/mis_turnos.py` makes the role dispatch (`odontologo` with `fecha` in `C-09`, extensible to `paciente` with `fecha_desde`/`fecha_hasta` in `C-10`) self-contained in one handler.
- **[Trade-off] Returning all 6 states (`solicitado`, `confirmado`, `presente`, `ausente`, `cancelado`, `anulado`)** → **Mitigation**: Gives the dentist complete visibility of their day's schedule (`US-007`), while the frontend (`C-15`) and backend state machine (`C-07`) restrict `presente`/`ausente` transitions strictly to `confirmado` appointments (`US-008 CA-2`).
