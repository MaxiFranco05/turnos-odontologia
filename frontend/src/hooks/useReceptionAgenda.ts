import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAgendaDia, updateTurnoEstado } from '@/services/reception.service';
import type {
  AgendaTurnoDiaItem,
  EstadoTurnoRecepcionTransicion,
  TurnoResponseItem,
} from '@/types/reception';

export interface UseAgendaDiaQueryOptions {
  fecha: string;
  odontologoId?: number | null;
}

export interface UpdateTurnoEstadoMutationVariables {
  turnoId: number;
  estado: EstadoTurnoRecepcionTransicion;
}

/**
 * Queries GET /api/agenda/dia using TanStack Query (Hard Rule #6: zero useEffect for fetching).
 */
export function useAgendaDiaQuery({ fecha, odontologoId }: UseAgendaDiaQueryOptions) {
  return useQuery<AgendaTurnoDiaItem[], Error>({
    queryKey: ['agenda-dia', fecha, odontologoId ?? 'all'],
    queryFn: () =>
      getAgendaDia({
        fecha,
        odontologo_id: odontologoId,
      }),
    enabled: Boolean(fecha),
  });
}

/**
 * Mutates appointment state via PATCH /api/turnos/{id} and invalidates ['agenda-dia'].
 */
export function useUpdateTurnoEstadoMutation() {
  const queryClient = useQueryClient();

  return useMutation<TurnoResponseItem, Error, UpdateTurnoEstadoMutationVariables>({
    mutationFn: ({ turnoId, estado }) =>
      updateTurnoEstado(turnoId, { estado }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['agenda-dia'] });
    },
  });
}
