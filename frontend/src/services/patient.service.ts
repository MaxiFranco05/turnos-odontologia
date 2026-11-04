import apiClient from '@/lib/api';
import type {
  DisponibilidadQueryParams,
  MisTurnosPacienteItem,
  MisTurnosPacienteQueryParams,
  SlotDisponibleItem,
  TurnoCancelPayload,
  TurnoCreatePayload,
  TurnoResponse,
} from '@/types/patient';

/**
 * Queries free appointment slots for a dentist and date via GET /api/disponibilidad (US-002).
 */
export async function getDisponibilidad(
  params: DisponibilidadQueryParams
): Promise<SlotDisponibleItem[]> {
  const response = await apiClient.get<SlotDisponibleItem[]>('/disponibilidad', {
    params: {
      odontologo_id: params.odontologo_id,
      fecha: params.fecha,
    },
  });
  return response.data;
}

/**
 * Creates an online appointment request in state 'solicitado' via POST /api/turnos (US-003, Hard Rules #1, #8).
 * Strips any undeclared properties to ensure strict compliance with TurnoCreate(extra="forbid").
 */
export async function createTurnoOnline(
  payload: TurnoCreatePayload
): Promise<TurnoResponse> {
  const strictBody: TurnoCreatePayload = {
    odontologo_id: Number(payload.odontologo_id),
    inicio: payload.inicio,
    fin: payload.fin,
    motivo: payload.motivo.trim(),
  };

  const response = await apiClient.post<TurnoResponse>('/turnos', strictBody);
  return response.data;
}

/**
 * Lists own appointments for the authenticated patient via GET /api/mis-turnos (US-004, RN-AU-02).
 * Never sends the dentist-only 'fecha' parameter.
 */
export async function getMisTurnosPaciente(
  params?: MisTurnosPacienteQueryParams
): Promise<MisTurnosPacienteItem[]> {
  const queryParams: Record<string, string> = {};

  if (params?.fecha_desde) {
    queryParams.fecha_desde = params.fecha_desde;
  }
  if (params?.fecha_hasta) {
    queryParams.fecha_hasta = params.fecha_hasta;
  }

  const response = await apiClient.get<MisTurnosPacienteItem[]>('/mis-turnos', {
    params: queryParams,
  });
  return response.data;
}

/**
 * Cancels a patient's own appointment via PATCH /api/turnos/{id} (RN-TU-04, Hard Rules #1, #8, #9).
 * Sends strictly { estado: 'cancelado' } matching TurnoEstadoUpdate(extra="forbid").
 */
export async function cancelarTurnoPaciente(
  turnoId: number
): Promise<TurnoResponse> {
  const strictBody: TurnoCancelPayload = {
    estado: 'cancelado',
  };

  const response = await apiClient.patch<TurnoResponse>(
    `/turnos/${turnoId}`,
    strictBody
  );
  return response.data;
}
