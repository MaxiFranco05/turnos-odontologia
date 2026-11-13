# Delta Spec: Odontólogo Calendario y Catálogo Dinámico de Odontólogos

## ADDED Requirements

### Requirement: Catálogo público de odontólogos (`GET /api/odontologos`)
El backend SHALL exponer `GET /api/odontologos` devolviendo exclusivamente usuarios con `rol == odontologo` ordenados por `id` ascendente, proyectando únicamente campos públicos (`id`, `nombre`, `email`, `nro_socio`, `especialidad`) bajo schema Pydantic con `extra="forbid"`.

#### Scenario: Listado de odontólogos sin exponer otros roles ni secretos
- **WHEN** un cliente consulta `GET /api/odontologos`
- **THEN** la respuesta HTTP 200 incluye solo usuarios con rol `odontologo` y omite `password_hash`, `debe_cambiar_password` y usuarios con rol `recepcion` o `paciente`.

### Requirement: Acceso directo al Calendario en el header del Odontólogo
El layout principal (`AppLayout`) SHALL mostrar el enlace `Calendario` (`/odontologo/calendario`) junto a `Mi agenda` (`/odontologo/agenda`) para usuarios autenticados con rol `odontologo`, tanto en la cápsula desktop como en el dock móvil.

#### Scenario: Navegación al calendario de confirmados desde el header
- **WHEN** el odontólogo hace clic en `Calendario` en la barra de navegación
- **THEN** navega a `/odontologo/calendario` y visualiza la grilla mensual interactiva junto con el listado filtrado de turnos en estado `confirmado` para la fecha seleccionada.

### Requirement: Reinicio limpio de secuencias e imágenes Docker aisladas
El script `seed_data(..., reset=True)` SHALL ejecutar `TRUNCATE TABLE turnos, plantillas_disponibilidad, usuarios RESTART IDENTITY CASCADE` cuando el motor sea PostgreSQL, y `frontend/.dockerignore` SHALL excluir `node_modules` y `dist` del contexto de build.

#### Scenario: Reseteo determinístico de IDs y build Docker limpio
- **WHEN** se ejecuta `seed.py --reset` contra PostgreSQL y se compila la imagen de `frontend`
- **THEN** los usuarios sembrados conservan IDs secuenciales `1..5` y la imagen Docker compila sin copiar `node_modules` del host.
