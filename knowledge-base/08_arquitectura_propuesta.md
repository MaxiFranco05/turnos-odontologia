# Arquitectura Propuesta

Propuesta inicial sobre el stack de cátedra (FastAPI + React + PostgreSQL).
Lo estructural respeta el Discovery; los detalles de sesión JWT se cierran
en Seguridad.

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| RBAC por rol | API: cada endpoint exige rol y alcance (propio vs. total) | Las transiciones de estado son por rol estricto (RN-GL-01) |
| Máquina de estados explícita | Entidad Turno + validación de transiciones en servidor | Evita estados imposibles y reparte permisos por actor |
| Invariante de servidor | Anti-solape + anticipación mínima validados transaccionalmente | El cliente nunca es confiable para reglas críticas |
| Derivación plantilla → huecos | Cálculo de disponibilidad en API, no turnos pre-generados | Mitiga «disponibilidad desactualizada» (riesgo del Discovery) |

## Estructura de directorios (propuesta, adaptar al stack)

```
proyecto/
├── backend/
│   └── app/
│       ├── domain/          # modelos SQLAlchemy: usuario, plantilla, turno, estados
│       ├── application/     # casos de uso (solicitar, confirmar, marcar, agenda)
│       ├── infrastructure/  # sesión de DB, auth JWT, dependencias FastAPI
│       ├── api/             # routers FastAPI por recurso (auth, disponibilidad, turnos, agenda)
│       └── main.py
├── frontend/
│   └── src/
│       ├── features/        # reserva, agenda-dia, mis-turnos, login
│       ├── shared/          # componentes y clientes API
│       └── pages/           # una página por vista de rol
└── docker-compose.yml       # api + postgres (+ redis, previsto v2+)
```

## Seguridad

- Autenticación: JWT con credenciales propias; claims `rol` + `user_id`;
  expiración a definir (`JWT_EXPIRE_MINUTES`); hash adaptativo (bcrypt) para
  contraseñas.
- Autorización: RBAC por rol + verificación de propiedad (odontólogo solo
  sus turnos, paciente solo los propios) en cada operación.
- Validación de input: en servidor para todo lo que toque reglas (solape,
  anticipación, transiciones); el cliente valida solo UX.
- Secrets management: secretos fuera del repo (variables de entorno);
  mecanismo concreto según despliegue a definir.

## Variables de entorno (propuesta inicial)

| Variable | Descripción | Sensible |
|---|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL | Sí |
| `JWT_SECRET` | Firma de tokens JWT | Sí |
| `JWT_EXPIRE_MINUTES` | Expiración del token | No |
| `REDIS_URL` | Cola/tareas (previsto v2+, sin uso en v1) | Sí |
| `CANCEL_MIN_HOURS` | Anticipación mínima de cancelación (RN-TU-05) | No |
| `TIMEZONE` | Zona horaria del consultorio (huecos y agenda) | No |
