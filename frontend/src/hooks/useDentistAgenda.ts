import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getMisTurnosCalendario,
  getMisTurnosOdontologo,
  updateTurnoAsistencia,
} from '@/services/dentist.service';
import type {
  CalendarioMesResponse,
  MisTurnosOdontologoItem,
  TurnoAsistenciaEstado,
  TurnoResponse,
} from '@/types/dentist';

export interface UpdateAsistenciaMutationVariables {
  turnoId: number;
  estado: TurnoAsistenciaEstado;
}

/**
 * Queries GET /api/mis-turnos?fecha=YYYY-MM-DD using TanStack Query (Hard Rule #6: zero useEffect for fetching).
 */
export function useDentistAgendaQuery(fecha: string) {
  return useQuery<MisTurnosOdontologoItem[], Error>({
    queryKey: ['dentist-agenda', { fecha }],
    queryFn: () => getMisTurnosOdontologo(fecha),
    enabled: Boolean(fecha),
  });
}

/**
 * Queries GET /api/mis-turnos/calendario using TanStack Query (C-22, Hard Rule #6).
 */
export function useDentistCalendarQuery(anio: number, mes: number) {
  return useQuery<CalendarioMesResponse, Error>({
    queryKey: ['dentist-calendar', { anio, mes }],
    queryFn: () => getMisTurnosCalendario(anio, mes),
    enabled: anio >= 2000 && mes >= 1 && mes <= 12,
  });
}

/**
 * Mutates appointment attendance via PATCH /api/turnos/{id} and invalidates
 * ['dentist-agenda'], ['dentist-calendar'], and ['agenda-dia'] caches.
 */
export function useUpdateAsistenciaMutation() {
  const queryClient = useQueryClient();

  return useMutation<TurnoResponse, Error, UpdateAsistenciaMutationVariables>({
    mutationFn: ({ turnoId, estado }) =>
      updateTurnoAsistencia(turnoId, { estado }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['dentist-agenda'] });
      void queryClient.invalidateQueries({ queryKey: ['dentist-calendar'] });
      void queryClient.invalidateQueries({ queryKey: ['agenda-dia'] });
    },
  });
}
