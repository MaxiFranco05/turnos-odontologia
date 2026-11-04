import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  useDisponibilidadQuery,
  useCreateTurnoMutation,
  useMisTurnosPacienteQuery,
  useCancelarTurnoMutation,
} from '@/hooks/usePatientPortal';
import * as patientService from '@/services/patient.service';
import type {
  SlotDisponibleItem,
  TurnoResponse,
  MisTurnosPacienteItem,
} from '@/types/patient';

vi.mock('@/services/patient.service', () => ({
  getDisponibilidad: vi.fn(),
  createTurnoOnline: vi.fn(),
  getMisTurnosPaciente: vi.fn(),
  cancelarTurnoPaciente: vi.fn(),
}));

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('usePatientPortal hooks (Strict TDD - C-13)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  it('useDisponibilidadQuery queries availability when odontologoId and fecha are provided', async () => {
    const mockSlots: SlotDisponibleItem[] = [
      {
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        odontologo_id: 2,
        prestacion: 'Consulta general',
      },
    ];

    vi.mocked(patientService.getDisponibilidad).mockResolvedValueOnce(mockSlots);

    const { result } = renderHook(
      () =>
        useDisponibilidadQuery({
          odontologoId: 2,
          fecha: '2026-11-23',
        }),
      { wrapper: createWrapper(queryClient) }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(patientService.getDisponibilidad).toHaveBeenCalledWith({
      odontologo_id: 2,
      fecha: '2026-11-23',
    });
    expect(result.current.data).toEqual(mockSlots);
  });

  it('useCreateTurnoMutation creates appointment and invalidates availability and self-appointment caches', async () => {
    const mockCreated: TurnoResponse = {
      id: 301,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-23T09:00:00-03:00',
      fin: '2026-11-23T09:30:00-03:00',
      motivo: 'Limpieza',
      estado: 'solicitado',
      origen: 'online',
    };

    vi.mocked(patientService.createTurnoOnline).mockResolvedValueOnce(mockCreated);
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useCreateTurnoMutation(), {
      wrapper: createWrapper(queryClient),
    });

    result.current.mutate({
      odontologo_id: 2,
      inicio: '2026-11-23T09:00:00-03:00',
      fin: '2026-11-23T09:30:00-03:00',
      motivo: 'Limpieza',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(patientService.createTurnoOnline).toHaveBeenCalledWith({
      odontologo_id: 2,
      inicio: '2026-11-23T09:00:00-03:00',
      fin: '2026-11-23T09:30:00-03:00',
      motivo: 'Limpieza',
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['patient-disponibilidad'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['patient-mis-turnos'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['agenda-dia'],
    });
  });

  it('useMisTurnosPacienteQuery queries patient self-appointments', async () => {
    const mockAppointments: MisTurnosPacienteItem[] = [
      {
        id: 301,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual',
        estado: 'solicitado',
        origen: 'online',
        odontologo: {
          id: 2,
          nombre: 'Dr. Martín Ruiz',
          nro_socio: null,
          email: 'martin.ruiz@clinica.com',
        },
      },
    ];

    vi.mocked(patientService.getMisTurnosPaciente).mockResolvedValueOnce(
      mockAppointments
    );

    const { result } = renderHook(
      () =>
        useMisTurnosPacienteQuery({
          fecha_desde: '2026-11-20',
          fecha_hasta: '2026-11-30',
        }),
      { wrapper: createWrapper(queryClient) }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(patientService.getMisTurnosPaciente).toHaveBeenCalledWith({
      fecha_desde: '2026-11-20',
      fecha_hasta: '2026-11-30',
    });
    expect(result.current.data).toEqual(mockAppointments);
  });

  it('useCancelarTurnoMutation cancels appointment and invalidates patient and availability caches', async () => {
    const mockCancelled: TurnoResponse = {
      id: 301,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-23T09:00:00-03:00',
      fin: '2026-11-23T09:30:00-03:00',
      motivo: 'Control anual',
      estado: 'cancelado',
      origen: 'online',
    };

    vi.mocked(patientService.cancelarTurnoPaciente).mockResolvedValueOnce(
      mockCancelled
    );
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useCancelarTurnoMutation(), {
      wrapper: createWrapper(queryClient),
    });

    result.current.mutate(301);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(patientService.cancelarTurnoPaciente).toHaveBeenCalledWith(301);
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['patient-mis-turnos'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['patient-disponibilidad'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['agenda-dia'],
    });
  });
});
