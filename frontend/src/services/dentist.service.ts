import apiClient from '@/lib/api';
import type {
  MisTurnosOdontologoItem,
  TurnoAsistenciaUpdateRequest,
  TurnoResponse,
} from '@/types/dentist';

/**
 * Queries GET /api/mis-turnos?fecha=YYYY-MM-DD for the authenticated dentist (US-007, RN-AU-02).
 * Never sends odontologo_id, fecha_desde, or fecha_hasta (enforced by C-09 backend contract).
 */
export async function getMisTurnosOdontologo(
  fecha: string
): Promise<MisTurnosOdontologoItem[]> {
  const response = await apiClient.get<MisTurnosOdontologoItem[]>('/mis-turnos', {
    params: { fecha },
  });
  return response.data;
}

/**
 * Records patient attendance via PATCH /api/turnos/{id} (US-008, RN-TU-03, Hard Rules #1, #8, #9).
 * Sends strictly { estado: 'presente' | 'ausente' } matching TurnoEstadoUpdate(extra="forbid").
 */
export async function updateTurnoAsistencia(
  turnoId: number,
  payload: TurnoAsistenciaUpdateRequest
): Promise<TurnoResponse> {
  const strictBody: TurnoAsistenciaUpdateRequest = {
    estado: payload.estado,
  };
  const response = await apiClient.patch<TurnoResponse>(
    `/turnos/${turnoId}`,
    strictBody
  );
  return response.data;
}
