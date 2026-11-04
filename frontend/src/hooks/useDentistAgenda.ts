import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getMisTurnosOdontologo,
  updateTurnoAsistencia,
} from '@/services/dentist.service';
import type {
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
 * Mutates appointment attendance via PATCH /api/turnos/{id} and invalidates
 * both ['dentist-agenda'] and ['agenda-dia'] caches.
 */
export function useUpdateAsistenciaMutation() {
  const queryClient = useQueryClient();

  return useMutation<TurnoResponse, Error, UpdateAsistenciaMutationVariables>({
    mutationFn: ({ turnoId, estado }) =>
      updateTurnoAsistencia(turnoId, { estado }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['dentist-agenda'] });
      void queryClient.invalidateQueries({ queryKey: ['agenda-dia'] });
    },
  });
}
