# Descripción General

## Stack tecnológico

| Capa | Tecnología | Estado |
|---|---|---|
| Frontend | React + TypeScript + Vite | Definido por cátedra |
| Backend | Python + FastAPI + SQLAlchemy (ORM) | Definido por cátedra |
| Base de datos | PostgreSQL | Definida por cátedra |
| Auth | JWT con credenciales propias (correo o N.º socio + contraseña) | Definido; esquema de sesión en `08` |
| Async (futuro) | Redis (recordatorios y tareas desde v2) | Previsto, no se usa en v1 |
| Entornos | Docker / Docker Compose (api + postgres + redis) | Definido por cátedra |

Stack definido por cátedra (ver DD-06 en `09_decisiones_y_supuestos.md`).
Redis queda reservado a funcionalidades asincrónicas de versiones
posteriores (recordatorios v2+); la v1 no lo utiliza.

## Arquitectura general

Arquitectura lógica (independiente del stack):

```
Paciente / Recepción / Odontólogo (navegador)
        │ login por rol + vistas según permiso
        ▼
API de turnos ──► invariantes de servidor (anti-solape, transiciones por rol)
        │
        ▼
Base de datos (usuarios, plantillas, turnos, estados)
```

Decisión de alto nivel: las reglas críticas (anti-solapamiento, transiciones
de estado por rol) viven en el servidor, nunca solo en el cliente — ningún
competidor relevado las publica como invariante verificable y es el
diferencial del proyecto (ver `09_decisiones_y_supuestos.md` DD-04).

## Integraciones externas

| Servicio | Propósito | Tipo | Estado |
|---|---|---|---|
| — | — | — | Ninguna obligatoria en v1 (decisión DD-01) |

Post-MVP previsto (no v1): recordatorios por email (WhatsApp a definir
luego), Mercado Pago (v2), PUCO/ARCA (v3).

## API REST (propuesta, a validar con el stack)

Recursos propuestos a partir de `04_modelo_de_datos.md`:

- `POST /auth/login` — inicio de sesión (correo o N.º socio + contraseña).
- `GET /disponibilidad?odontologo=&desde=&hasta=` — huecos derivados de
  plantilla.
- `POST /turnos` — solicitar turno (paciente; crea en estado `solicitado`).
- `PATCH /turnos/{id}/confirmar` — recepción.
- `PATCH /turnos/{id}/anular` — recepción (con anticipación mínima RN-TU-05).
- `PATCH /turnos/{id}/ausentismo` — paciente avisa que no asistirá.
- `PATCH /turnos/{id}/presente|ausente` — odontólogo sobre SUS turnos.
- `GET /agenda?dia=` — recepción (todos); odontólogo (solo propios).
