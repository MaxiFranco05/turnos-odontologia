import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  useDentistAgendaQuery,
  useUpdateAsistenciaMutation,
} from '@/hooks/useDentistAgenda';
import * as dentistService from '@/services/dentist.service';
import type { MisTurnosOdontologoItem, TurnoResponse } from '@/types/dentist';

vi.mock('@/services/dentist.service', () => ({
  getMisTurnosOdontologo: vi.fn(),
  updateTurnoAsistencia: vi.fn(),
}));

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useDentistAgenda hooks (Strict TDD - C-15)', () => {
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

  it('useDentistAgendaQuery fetches daily agenda via getMisTurnosOdontologo without useEffect (Hard Rule #6)', async () => {
    const mockTurnos: MisTurnosOdontologoItem[] = [
      {
        id: 501,
        paciente_id: 20,
        odontologo_id: 7,
        inicio: '2026-11-10T09:00:00Z',
        fin: '2026-11-10T09:30:00Z',
        motivo: 'Control general',
        estado: 'confirmado',
        origen: 'online',
        paciente: {
          id: 20,
          nombre: 'Lucía Gómez',
          nro_socio: 'SOC-1001',
          email: 'lucia.gomez@example.com',
        },
      },
    ];

    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValueOnce(
      mockTurnos
    );

    const { result } = renderHook(() => useDentistAgendaQuery('2026-11-10'), {
      wrapper: createWrapper(queryClient),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(dentistService.getMisTurnosOdontologo).toHaveBeenCalledWith(
      '2026-11-10'
    );
    expect(result.current.data).toEqual(mockTurnos);
  });

  it('useUpdateAsistenciaMutation calls updateTurnoAsistencia and invalidates ["dentist-agenda"] and ["agenda-dia"]', async () => {
    const mockUpdated: TurnoResponse = {
      id: 501,
      paciente_id: 20,
      odontologo_id: 7,
      inicio: '2026-11-10T09:00:00Z',
      fin: '2026-11-10T09:30:00Z',
      motivo: 'Control general',
      estado: 'presente',
      origen: 'online',
    };

    vi.mocked(dentistService.updateTurnoAsistencia).mockResolvedValueOnce(
      mockUpdated
    );
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useUpdateAsistenciaMutation(), {
      wrapper: createWrapper(queryClient),
    });

    result.current.mutate({ turnoId: 501, estado: 'presente' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(dentistService.updateTurnoAsistencia).toHaveBeenCalledWith(501, {
      estado: 'presente',
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['dentist-agenda'],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['agenda-dia'],
    });
  });
});
