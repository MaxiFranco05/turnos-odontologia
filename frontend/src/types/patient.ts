import type {
  EstadoTurno,
  OrigenTurno,
  TurnoResponseItem,
} from '@/types/reception';

export type TurnoResponse = TurnoResponseItem;

export interface SlotDisponibleItem {
  inicio: string; // ISO datetime string with clinic timezone offset
  fin: string;    // ISO datetime string with clinic offset
  odontologo_id: number;
  prestacion: string;
}

export interface DisponibilidadQueryParams {
  odontologo_id: number;
  fecha: string; // YYYY-MM-DD
}

export interface TurnoCreatePayload {
  odontologo_id: number;
  inicio: string;
  fin: string;
  motivo: string;
}

export interface TurnoOdontologoResumen {
  id: number;
  nombre: string;
  nro_socio: string | null;
  email: string | null;
}

export interface MisTurnosPacienteItem {
  id: number;
  paciente_id: number;
  odontologo_id: number;
  inicio: string;
  fin: string;
  motivo: string;
  estado: EstadoTurno;
  origen: OrigenTurno;
  odontologo: TurnoOdontologoResumen;
}

export interface MisTurnosPacienteQueryParams {
  fecha_desde?: string; // YYYY-MM-DD
  fecha_hasta?: string; // YYYY-MM-DD
}

export interface TurnoCancelPayload {
  estado: 'cancelado';
}
