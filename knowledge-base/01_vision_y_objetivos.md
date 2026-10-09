# Visión y Objetivos

## Propósito del sistema

Eliminar la coordinación manual de turnos odontológicos (WhatsApp y papel),
que genera dobles reservas y tiempo perdido confirmando cada turno, mediante
un sistema con reserva online, agenda por odontólogo y reglas de estado por
rol.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Paciente | Solicitar turnos sin llamar ni escribir por WhatsApp | Cancelar turnos propios para liberar el horario |
| Recepción | Gestionar la agenda del día sin papel ni chat disperso | Confirmar y anular turnos solicitados |
| Odontólogo | Ver solo SUS turnos y saber a quién atiende | Marcar presente/ausente sobre sus turnos |

## Alcance v1

- Solicitud de turno online por el paciente con login (correo o N.º de
  socio/afiliado + contraseña).
- Disponibilidad derivada de la plantilla del odontólogo (días, horarios,
  duración por prestación).
- Agenda del día para recepción (todos los odontólogos) y por odontólogo
  (solo sus turnos).
- Máquina de estados mínima con transiciones por rol estricta.
- Regla anti-solapamiento por odontólogo como invariante de servidor.
- Anticipación mínima configurable para cancelación/anulación.
- Modo «solicitud sujeta a confirmación» con marcado visual del origen
  online.

## Fuera de alcance

- Odontograma, historia clínica, CDSS/IA diagnóstica.
- Recordatorios automáticos por email (post-MVP; WhatsApp a definir luego).
- Reprogramación autogestionada y lista de espera (v2).
- Señas y cobros con Mercado Pago (v2).
- Obras sociales, verificación PUCO, factura electrónica ARCA (v3).
- Marketing multicanal, multi-sede, firma certificada.

## Métricas de éxito (propuestas)

- Cero dobles reservas por solapamiento (regla de servidor).
- Reducción de ausentismo no avisado frente a la operatoria manual.
- Porcentaje de turnos solicitados por el canal online frente a WhatsApp.
