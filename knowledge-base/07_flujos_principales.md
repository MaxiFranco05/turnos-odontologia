# Flujos Principales

Cada flujo se documenta extremo a extremo, mostrando interacciones entre
componentes. Componentes genéricos (válidos para cualquier stack):
`Navegador → API → Reglas → DB`.

## Flujo 1: Iniciar sesión

**Disparador**: el usuario abre el sistema sin sesión.
**Actor**: paciente, recepción u odontólogo.

**Pasos**:

1. Navegador muestra formulario (identificador + contraseña).
2. API verifica credencial contra `Usuario` (correo o N.º socio).
3. API crea la sesión y responde con el rol.
4. Navegador redirige a la vista del rol; si la cuenta tiene
   `debe_cambiar_password`, deriva al cambio obligatorio (US-010) antes de
   operar.

**Casos de error**:

- Credencial inválida → mensaje genérico, sin revelar qué falló (RN-AU-01).
- Cuenta sin rol asignado → acceso denegado, registrar en log.

## Flujo 2: Solicitar turno (paciente)

**Disparador**: paciente autenticado busca un horario.
**Actor**: paciente.

**Pasos**:

1. Navegador pide huecos (`GET /disponibilidad`) derivados de plantilla.
2. API calcula huecos libres (plantilla menos turnos vigentes).
3. Paciente elige un hueco y confirma.
4. API crea el turno en `solicitado` dentro de una transacción que
   re-chequea solape (RN-AG-01).
5. Navegador muestra confirmación de solicitud (no de turno confirmado).

**Casos de error**:

- Hueco tomado concurrentemente → error «ya ocupado», ofrecer alternativas.
- Horario fuera de plantilla o pasado → rechazo (RN-AG-02, RN-GL-02).

## Flujo 3: Confirmar / anular (recepción)

**Disparador**: turno en `solicitado` visible en agenda del día.
**Actor**: recepción.

**Pasos**:

1. Navegador muestra agenda del día con estados y origen online.
2. Recepción confirma → API transiciona `solicitado → confirmado`.
3. Recepción anula → API verifica anticipación mínima (RN-TU-05) y
   transiciona a `anulado`, liberando el hueco.

**Casos de error**:

- Anulación dentro de la anticipación mínima → rechazo con el plazo
  exigido.
- Transición inválida (ej. confirmar un turno ya anulado) → rechazo.

## Flujo 4: Presente / ausente (odontólogo)

**Disparador**: turno confirmado del día.
**Actor**: odontólogo, solo sobre SUS turnos.

**Pasos**:

1. Navegador muestra solo los turnos propios del odontólogo.
2. Odontólogo marca `presente` o `ausente`.
3. API valida propiedad del turno y registra el estado final.

**Casos de error**:

- Turno de otro odontólogo → 403 (RN-AU-02, RN-GL-01).

## Flujo 5: Cancelar turno (paciente)

**Disparador**: paciente no podrá asistir.
**Actor**: paciente, sobre turno propio futuro.

**Pasos**:

1. Navegador lista «mis turnos» futuros.
2. Paciente cancela → API verifica anticipación de 24 h (RN-TU-05) y marca
   `cancelado`, liberando el hueco para recepción.

**Casos de error**:

- Turno ajeno o pasado → rechazo.
- Dentro de las 24 h → rechazo con el plazo exigido.
