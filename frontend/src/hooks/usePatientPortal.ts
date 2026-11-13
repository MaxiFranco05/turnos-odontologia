import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDisponibilidad,
  createTurnoOnline,
  getMisTurnosPaciente,
  cancelarTurnoPaciente,
  getOdontologos,
  type OdontologoItem,
} from '@/services/patient.service';
import type {
  MisTurnosPacienteItem,
  MisTurnosPacienteQueryParams,
  SlotDisponibleItem,
  TurnoCreatePayload,
  TurnoResponse,
} from '@/types/patient';

/**
 * Queries active dentists in the clinic via GET /api/odontologos.
 */
export function useOdontologosQuery() {
  return useQuery<OdontologoItem[], Error>({
    queryKey: ['odontologos-list'],
    queryFn: getOdontologos,
    staleTime: 1000 * 60 * 10,
  });
}

export interface UseDisponibilidadQueryOptions {
  odontologoId?: number;
  fecha?: string;
  enabled?: boolean;
}

/**
 * Queries free appointment slots for a given dentist and date using TanStack Query (Hard Rule #6).
 */
export function useDisponibilidadQuery({
  odontologoId,
  fecha,
  enabled,
}: UseDisponibilidadQueryOptions) {
  const isQueryEnabled =
    enabled !== undefined
      ? enabled
      : Boolean(odontologoId && odontologoId > 0 && fecha);

  return useQuery<SlotDisponibleItem[], Error>({
    queryKey: ['patient-disponibilidad', { odontologoId, fecha }],
    queryFn: () =>
      getDisponibilidad({
        odontologo_id: odontologoId!,
        fecha: fecha!,
      }),
    enabled: isQueryEnabled,
  });
}

/**
 * Mutates an online appointment reservation (POST /api/turnos) and invalidates
 * availability and appointment caches across patient and reception views.
 */
export function useCreateTurnoMutation() {
  const queryClient = useQueryClient();

  return useMutation<TurnoResponse, Error, TurnoCreatePayload>({
    mutationFn: (payload) => createTurnoOnline(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['patient-disponibilidad'] });
      void queryClient.invalidateQueries({ queryKey: ['patient-mis-turnos'] });
      void queryClient.invalidateQueries({ queryKey: ['agenda-dia'] });
    },
  });
}

/**
 * Queries the authenticated patient's own appointments using TanStack Query (Hard Rule #6).
 */
export function useMisTurnosPacienteQuery(params?: MisTurnosPacienteQueryParams) {
  return useQuery<MisTurnosPacienteItem[], Error>({
    queryKey: ['patient-mis-turnos', { fecha_desde: params?.fecha_desde, fecha_hasta: params?.fecha_hasta }],
    queryFn: () => getMisTurnosPaciente(params),
  });
}

/**
 * Cancels a patient's own appointment (PATCH /api/turnos/{id} with estado='cancelado') and
 * invalidates patient appointments and availability slots so the slot is freed up.
 */
export function useCancelarTurnoMutation() {
  const queryClient = useQueryClient();

  return useMutation<TurnoResponse, Error, number>({
    mutationFn: (turnoId) => cancelarTurnoPaciente(turnoId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['patient-mis-turnos'] });
      void queryClient.invalidateQueries({ queryKey: ['patient-disponibilidad'] });
      void queryClient.invalidateQueries({ queryKey: ['agenda-dia'] });
    },
  });
}
