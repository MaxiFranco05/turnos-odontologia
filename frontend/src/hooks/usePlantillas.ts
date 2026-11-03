import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPlantillas,
  createPlantilla,
  updatePlantilla,
  deletePlantilla,
} from '@/services/reception.service';
import type {
  PlantillaCreatePayload,
  PlantillaItem,
  PlantillaUpdatePayload,
} from '@/types/reception';

export interface UpdatePlantillaMutationVariables {
  plantillaId: number;
  payload: PlantillaUpdatePayload;
}

/**
 * Queries GET /api/plantillas[?odontologo_id=N] using TanStack Query (Hard Rule #6: zero useEffect).
 */
export function usePlantillasQuery(odontologoId?: number | null) {
  return useQuery<PlantillaItem[], Error>({
    queryKey: ['plantillas', odontologoId ?? 'all'],
    queryFn: () => getPlantillas(odontologoId),
  });
}

/**
 * Creates an availability template via POST /api/plantillas and invalidates ['plantillas'].
 */
export function useCreatePlantillaMutation() {
  const queryClient = useQueryClient();

  return useMutation<PlantillaItem, Error, PlantillaCreatePayload>({
    mutationFn: (payload) => createPlantilla(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantillas'] });
    },
  });
}

/**
 * Partially updates an availability template via PATCH /api/plantillas/{id} and invalidates ['plantillas'].
 */
export function useUpdatePlantillaMutation() {
  const queryClient = useQueryClient();

  return useMutation<PlantillaItem, Error, UpdatePlantillaMutationVariables>({
    mutationFn: ({ plantillaId, payload }) => updatePlantilla(plantillaId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantillas'] });
    },
  });
}

/**
 * Deletes an availability template via DELETE /api/plantillas/{id} and invalidates ['plantillas'].
 */
export function useDeletePlantillaMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (plantillaId) => deletePlantilla(plantillaId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantillas'] });
    },
  });
}
