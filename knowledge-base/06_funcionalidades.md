# Funcionalidades

Organizadas por **épica** y luego por **historia de usuario** (formato US-NNN).

## Épica 1: Acceso

### US-001 — Iniciar sesión

**Como** paciente, recepción u odontólogo
**Quiero** ingresar con mi correo o N.º de socio + contraseña
**Para** operar según mi rol

**Criterios de aceptación**:

- [ ] CA-1: login exitoso con correo o con N.º de socio indistintamente.
- [ ] CA-2: credencial inválida no revela si el identificador existe.
- [ ] CA-3: cada rol aterriza en su vista (mis turnos / agenda del día /
  mis turnos como odontólogo).

**Reglas relacionadas**: RN-AU-01, RN-AU-02

### US-010 — Cambio obligatorio de contraseña temporal

**Como** paciente con cuenta recién creada por recepción
**Quiero** que el primer login me obligue a cambiar la contraseña y
completar mis datos obligatorios
**Para** tomar control de mi cuenta (los sensibles los completo yo)

**Criterios de aceptación**:

- [ ] CA-1: con `debe_cambiar_password` en verdadero, el login deriva al
  cambio antes de cualquier otra acción.
- [ ] CA-2: hasta completar el cambio, ninguna otra operación está
  disponible.
- [ ] CA-3: al completar, el flag se apaga y `perfil_completo` refleja los
  datos cargados.

**Reglas relacionadas**: RN-AU-01, RN-AU-02

## Épica 2: Reserva del paciente

### US-002 — Ver horarios libres

**Como** paciente
**Quiero** ver los huecos disponibles por odontólogo y fecha
**Para** elegir sin llamar ni escribir por WhatsApp

**Criterios de aceptación**:

- [ ] CA-1: solo muestra huecos derivados de plantilla, sin solapes.
- [ ] CA-2: no muestra turnos de otros pacientes.

**Reglas relacionadas**: RN-AG-01, RN-AG-02

### US-003 — Solicitar turno

**Como** paciente
**Quiero** solicitar un hueco libre
**Para** reservar mi atención (queda en estado `solicitado`)

**Criterios de aceptación**:

- [ ] CA-1: el turno nace en `solicitado`, nunca confirmado directo
  (modo solicitud a confirmar).
- [ ] CA-2: la solicitud incluye el motivo (tipo de consulta descrito por
  el paciente, texto libre).
- [ ] CA-3: el hueco deja de ofrecerse (sin doble reserva, ni concurrente).
- [ ] CA-3: el paciente ve el origen online marcado en su turno.

**Reglas relacionadas**: RN-TU-01, RN-AG-01

### US-004 — Avisar ausentismo

**Como** paciente
**Quiero** cancelar un turno propio con 24 h de anticipación
**Para** liberar el horario

**Criterios de aceptación**:

- [ ] CA-1: solo sobre turnos propios futuros.
- [ ] CA-2: respeta la anticipación mínima de 24 h (RN-TU-05).
- [ ] CA-3: el turno pasa a `cancelado` (distinto de `anulado` de recepción).

**Reglas relacionadas**: RN-TU-04, RN-TU-05

## Épica 3: Gestión del consultorio

### US-005 — Ver agenda del día (recepción)

**Como** recepción
**Quiero** ver la agenda del día de todos los odontólogos
**Para** confirmar y anular turnos solicitados

**Criterios de aceptación**:

- [ ] CA-1: muestra estados con origen online marcado.
- [ ] CA-2: incluye ausentismos avisados por pacientes.

**Reglas relacionadas**: RN-TU-02

### US-006 — Confirmar / anular turno

**Como** recepción
**Quiero** confirmar o anular un turno solicitado
**Para** validar la agenda

**Criterios de aceptación**:

- [ ] CA-1: confirmar pasa `solicitado → confirmado`.
- [ ] CA-2: anular respeta anticipación mínima y libera el hueco.

**Reglas relacionadas**: RN-TU-02, RN-TU-05

### US-007 — Ver mis turnos (odontólogo)

**Como** odontólogo
**Quiero** ver la agenda de MIS turnos del día
**Para** saber a quién atiendo y a qué hora

**Criterios de aceptación**:

- [ ] CA-1: nunca muestra turnos de otros odontólogos.

**Reglas relacionadas**: RN-AU-02

### US-008 — Marcar presente / ausente

**Como** odontólogo
**Quiero** indicar el estado de mis turnos
**Para** registrar asistencia real

**Criterios de aceptación**:

- [ ] CA-1: solo sobre turnos propios.
- [ ] CA-2: transitions válidas desde `confirmado`.

**Reglas relacionadas**: RN-TU-03

## Épica 4: Integridad de agenda

### US-009 — Anti-solapamiento de servidor

**Como** sistema
**Quiero** rechazar cualquier turno que intersecte otro vigente del mismo
odontólogo
**Para** garantizar cero dobles reservas aunque el cliente falle o haya
concurrencia

**Criterios de aceptación**:

- [ ] CA-1: constraint a nivel de persistencia + validación transaccional.
- [ ] CA-2: el error es claro (hueco ya ocupado) y no deja datos parciales.

**Reglas relacionadas**: RN-AG-01
