import type {
  EstadoTurno,
  OrigenTurno,
  ParticipantePacienteResumen,
  TurnoResponseItem,
} from '@/types/reception';

export type TurnoEstado = EstadoTurno;
export type TurnoOrigen = OrigenTurno;
export type TurnoResponse = TurnoResponseItem;
export type TurnoPacienteResumen = ParticipantePacienteResumen;

export interface MisTurnosOdontologoItem {
  id: number;
  paciente_id: number;
  odontologo_id: number;
  inicio: string;
  fin: string;
  motivo: string;
  estado: EstadoTurno;
  origen: OrigenTurno;
  paciente: TurnoPacienteResumen;
}

export type TurnoAsistenciaEstado = 'presente' | 'ausente';

export interface TurnoAsistenciaUpdateRequest {
  estado: TurnoAsistenciaEstado;
}

export interface CalendarioDiaResumen {
  fecha: string;
  confirmados: number;
  solicitados: number;
  atendidos: number;
  total_activos: number;
}

export interface CalendarioMesResponse {
  anio: number;
  mes: number;
  dias: CalendarioDiaResumen[];
}
