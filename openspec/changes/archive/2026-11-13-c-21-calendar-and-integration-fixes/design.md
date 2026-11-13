# Design: C-21 Calendario de Confirmados e Integración Fullstack

## Decisions

1. **Endpoint `GET /api/odontologos` (`backend/app/api/odontologos.py`)**:
   - URI basada en sustantivo (Regla Dura #8).
   - Consulta SQLAlchemy 2.0 `select(Usuario).where(Usuario.rol == RolUsuario.ODONTOLOGO)` (Regla Dura #2).
   - Schema `OdontologoPublicResponse` con `ConfigDict(extra="forbid", from_attributes=True)` (Regla Dura #1).
   - Limpia sufijos sintéticos `(Ficticia)` / `(Ficticio)` para presentación en UI manteniendo datos ficticios (Regla Dura #12).

2. **Navegación del Calendario en Header (`AppLayout.tsx` + `routes.tsx` + `OdontologoAgendaPage.tsx`)**:
   - Se evitó duplicar controles en el cuerpo de `OdontologoAgendaPage`: el cambio entre `Mi agenda` y `Calendario` se realiza exclusivamente desde la cápsula del header mediante rutas `/odontologo/agenda` y `/odontologo/calendario`.
   - `OdontologoAgendaPage` sincroniza su vista activa leyendo `useLocation().pathname` y reutiliza `useDentistAgendaQuery(fecha)` (TanStack Query, Regla Dura #6), filtrando `estado === 'confirmado'` en la vista calendario.

3. **Selector dinámico en Paciente (`PacienteDisponibilidadPage.tsx`)**:
   - Consume `useOdontologosQuery()` y toma por defecto el primer ID real devuelto por el backend (`odontologosQuery.data[0].id`), evitando desfasajes si las secuencias de DB cambian.

4. **Docker & Seed**:
   - `frontend/.dockerignore` y `backend/.dockerignore` evitan sobreescribir `node_modules` de Linux Alpine con binarios de Windows (`node.exe: not found`).
   - `seed.py` usa `TRUNCATE ... RESTART IDENTITY CASCADE` únicamente sobre dialecto `postgresql` manteniendo `delete()` sobre SQLite para no alterar `test_seed_script.py`.

## UI Mockups

Decision: no (project policy)
