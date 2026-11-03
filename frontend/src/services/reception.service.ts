import apiClient from '@/lib/api';
import type {
  AgendaDiaQueryParams,
  AgendaTurnoDiaItem,
  PlantillaCreatePayload,
  PlantillaItem,
  PlantillaUpdatePayload,
  TurnoEstadoUpdatePayload,
  TurnoResponseItem,
} from '@/types/reception';

/**
 * Formats a Date object as local YYYY-MM-DD without UTC offset drift.
 */
export function formatLocalDateISO(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Normalizes backend time strings ('08:00:00' or '08:00') to 'HH:MM'.
 */
export function normalizeTimeHHMM(timeStr: string): string {
  if (!timeStr) return '';
  const parts = timeStr.trim().split(':');
  if (parts.length >= 2) {
    return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
  }
  return timeStr.trim();
}

/**
 * Formats an ISO datetime string into a readable HH:MM range or local time.
 */
export function formatTimeFromISO(isoString: string): string {
  if (!isoString) return '';
  const timeMatch = isoString.match(/T(\d{2}:\d{2})/);
  if (timeMatch) {
    return timeMatch[1];
  }
  const parsed = new Date(isoString);
  if (Number.isNaN(parsed.getTime())) return isoString;
  const hours = String(parsed.getHours()).padStart(2, '0');
  const minutes = String(parsed.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

/**
 * Extracts a user-friendly error message from an Axios/API error without using `any`.
 */
export function extractApiErrorMessage(
  error: unknown,
  fallback: string = 'Ocurrió un error al procesar la solicitud.'
): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { status?: number; data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first && typeof first.msg === 'string') {
        return first.msg;
      }
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

/**
 * Queries GET /api/agenda/dia?fecha=YYYY-MM-DD[&odontologo_id=N] (US-005, RN-GL-01).
 */
export async function getAgendaDia(
  params: AgendaDiaQueryParams
): Promise<AgendaTurnoDiaItem[]> {
  const queryParams: Record<string, string | number> = {
    fecha: params.fecha,
  };
  if (params.odontologo_id !== undefined && params.odontologo_id !== null) {
    queryParams.odontologo_id = params.odontologo_id;
  }

  const response = await apiClient.get<AgendaTurnoDiaItem[]>('/agenda/dia', {
    params: queryParams,
  });
  return response.data;
}

/**
 * Updates appointment state via PATCH /api/turnos/{id} (Hard Rules #1, #8, #9).
 * Sends strictly { estado: 'confirmado' | 'anulado' } matching TurnoEstadoUpdate(extra="forbid").
 */
export async function updateTurnoEstado(
  turnoId: number,
  payload: TurnoEstadoUpdatePayload
): Promise<TurnoResponseItem> {
  const strictBody: TurnoEstadoUpdatePayload = {
    estado: payload.estado,
  };
  const response = await apiClient.patch<TurnoResponseItem>(
    `/turnos/${turnoId}`,
    strictBody
  );
  return response.data;
}

/**
 * Queries GET /api/plantillas[?odontologo_id=N] (US-006).
 */
export async function getPlantillas(
  odontologoId?: number | null
): Promise<PlantillaItem[]> {
  const params: Record<string, number> = {};
  if (odontologoId !== undefined && odontologoId !== null) {
    params.odontologo_id = odontologoId;
  }
  const response = await apiClient.get<PlantillaItem[]>('/plantillas', { params });
  return response.data;
}

/**
 * Creates a new availability template via POST /api/plantillas (extra="forbid").
 */
export async function createPlantilla(
  payload: PlantillaCreatePayload
): Promise<PlantillaItem> {
  const strictBody: PlantillaCreatePayload = {
    odontologo_id: Number(payload.odontologo_id),
    dia_semana: Number(payload.dia_semana),
    hora_inicio: normalizeTimeHHMM(payload.hora_inicio),
    hora_fin: normalizeTimeHHMM(payload.hora_fin),
    duracion_slot_minutos: Number(payload.duracion_slot_minutos),
    prestacion: payload.prestacion.trim(),
  };
  const response = await apiClient.post<PlantillaItem>('/plantillas', strictBody);
  return response.data;
}

/**
 * Partially updates an existing template via PATCH /api/plantillas/{id} (Hard Rules #1, #9).
 * Omits immutable fields (id, odontologo_id) and undefined properties.
 */
export async function updatePlantilla(
  plantillaId: number,
  payload: PlantillaUpdatePayload
): Promise<PlantillaItem> {
  const strictBody: PlantillaUpdatePayload = {};

  if (payload.dia_semana !== undefined) {
    strictBody.dia_semana = Number(payload.dia_semana);
  }
  if (payload.hora_inicio !== undefined) {
    strictBody.hora_inicio = normalizeTimeHHMM(payload.hora_inicio);
  }
  if (payload.hora_fin !== undefined) {
    strictBody.hora_fin = normalizeTimeHHMM(payload.hora_fin);
  }
  if (payload.duracion_slot_minutos !== undefined) {
    strictBody.duracion_slot_minutos = Number(payload.duracion_slot_minutos);
  }
  if (payload.prestacion !== undefined) {
    strictBody.prestacion = payload.prestacion.trim();
  }

  const response = await apiClient.patch<PlantillaItem>(
    `/plantillas/${plantillaId}`,
    strictBody
  );
  return response.data;
}

/**
 * Deletes an availability template via DELETE /api/plantillas/{id} (204 No Content).
 */
export async function deletePlantilla(plantillaId: number): Promise<void> {
  await apiClient.delete(`/plantillas/${plantillaId}`);
}
