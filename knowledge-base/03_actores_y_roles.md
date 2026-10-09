# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Paciente | Persona con turno o que solicita uno; accede con correo o N.º de socio/afiliado + contraseña | Reserva online describiendo el tipo de consulta, ve sus turnos, cancela los propios |
| Recepción | Personal del consultorio que gestiona la agenda | Ve agenda del día completa, confirma y anula turnos, edita plantillas, crea cuentas |
| Odontólogo | Profesional que atiende | Ve solo SUS turnos, marca presente/ausente |

## RBAC — Matriz de permisos

| Rol | Turno propio | Turno ajeno | Agenda del día | Plantilla de disponibilidad | Usuarios |
|---|---|---|---|---|---|
| Paciente | Solicitar, avisar ausentismo | — | Ver huecos libres | Solo lectura (huecos) | Ver/editar solo su cuenta |
| Recepción | Confirmar, anular | Confirmar, anular (todos) | Lectura total | Creación y edición | Crear cuentas de paciente |
| Odontólogo | Marcar presente/ausente (solo SUS turnos) | — | Lectura solo propios | Lectura propia | — |

Toda transición fuera de rol se rechaza en el servidor (RN-GL-01).

## Alta de cuentas

Las cuentas de paciente las crea **recepción** con datos esenciales (nombre,
N.º paciente, correo/contacto) y contraseña temporal con flag
`debe_cambiar_password`. El primer login obliga a cambiarla y completar los
datos obligatorios; los datos personales y sensibles los llena el paciente
en su perfil (DD-07).

## Rutas públicas

- `/login` — inicio de sesión (pública). Si la cuenta tiene contraseña
  temporal, el login deriva al cambio obligatorio antes de operar.
- No hay auto-registro público: el alta es por recepción (DD-07). Hasta
  definir lo contrario, ninguna otra ruta es pública: reserva, agenda y
  gestión exigen sesión.
