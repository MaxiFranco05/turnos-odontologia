export type EstadoTurno =
  | 'solicitado'
  | 'confirmado'
  | 'anulado'
  | 'cancelado'
  | 'presente'
  | 'ausente';

export type OrigenTurno = 'online' | 'recepcion';

export type EstadoTurnoRecepcionTransicion = 'confirmado' | 'anulado';

export interface ParticipantePacienteResumen {
  id: number;
  nombre: string;
  nro_socio: string | null;
  email: string | null;
}

export interface ParticipanteOdontologoResumen {
  id: number;
  nombre: string;
  email: string | null;
}

export interface AgendaTurnoDiaItem {
  id: number;
  paciente_id: number;
  odontologo_id: number;
  inicio: string;
  fin: string;
  motivo: string;
  estado: EstadoTurno;
  origen: OrigenTurno;
  paciente: ParticipantePacienteResumen;
  odontologo: ParticipanteOdontologoResumen;
}

export interface AgendaDiaQueryParams {
  fecha: string;
  odontologo_id?: number | null;
}

export interface TurnoEstadoUpdatePayload {
  estado: EstadoTurnoRecepcionTransicion;
}

export interface TurnoResponseItem {
  id: number;
  paciente_id: number;
  odontologo_id: number;
  inicio: string;
  fin: string;
  motivo: string;
  estado: EstadoTurno;
  origen: OrigenTurno;
}

export interface PlantillaItem {
  id: number;
  odontologo_id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  duracion_slot_minutos: number;
  prestacion: string;
}

export interface PlantillaCreatePayload {
  odontologo_id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  duracion_slot_minutos: number;
  prestacion: string;
}

export interface PlantillaUpdatePayload {
  dia_semana?: number;
  hora_inicio?: string;
  hora_fin?: string;
  duracion_slot_minutos?: number;
  prestacion?: string;
}

export const DIAS_SEMANA_LABELS: Record<number, string> = {
  0: 'Lunes',
  1: 'Martes',
  2: 'Miércoles',
  3: 'Jueves',
  4: 'Viernes',
  5: 'Sábado',
  6: 'Domingo',
};

export const ESTADO_TURNO_LABELS: Record<EstadoTurno, string> = {
  solicitado: 'Solicitado',
  confirmado: 'Confirmado',
  anulado: 'Anulado',
  cancelado: 'Cancelado',
  presente: 'Presente',
  ausente: 'Ausente',
};

export const ORIGEN_TURNO_LABELS: Record<OrigenTurno, string> = {
  online: 'Online',
  recepcion: 'Recepción',
};
