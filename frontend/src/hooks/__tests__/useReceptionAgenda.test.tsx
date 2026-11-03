import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  useAgendaDiaQuery,
  useUpdateTurnoEstadoMutation,
} from '@/hooks/useReceptionAgenda';
import * as receptionService from '@/services/reception.service';
import type { AgendaTurnoDiaItem, TurnoResponseItem } from '@/types/reception';

vi.mock('@/services/reception.service', () => ({
  getAgendaDia: vi.fn(),
  updateTurnoEstado: vi.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

  const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { wrapper, queryClient, invalidateSpy };
}

describe('useReceptionAgenda hooks (Strict TDD - C-14 / Hard Rule #6)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('useAgendaDiaQuery fetches daily agenda by fecha and optional odontologoId', async () => {
    const sampleAgenda: AgendaTurnoDiaItem[] = [
      {
        id: 1,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-20T09:00:00Z',
        fin: '2026-11-20T09:30:00Z',
        motivo: 'Consulta general',
        estado: 'solicitado',
        origen: 'online',
        paciente: {
          id: 10,
          nombre: 'Lucía Gómez',
          nro_socio: 'SOC-1001',
          email: 'lucia.gomez@example.com',
        },
        odontologo: {
          id: 2,
          nombre: 'Dr. Martín Ruiz',
          email: 'martin.ruiz@clinica.com',
        },
      },
    ];
    vi.mocked(receptionService.getAgendaDia).mockResolvedValueOnce(sampleAgenda);

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useAgendaDiaQuery({ fecha: '2026-11-20', odontologoId: 2 }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.getAgendaDia).toHaveBeenCalledWith({
      fecha: '2026-11-20',
      odontologo_id: 2,
    });
    expect(result.current.data).toEqual(sampleAgenda);
  });

  it('useUpdateTurnoEstadoMutation updates state and invalidates ["agenda-dia"] queries', async () => {
    const updatedTurno: TurnoResponseItem = {
      id: 1,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-20T09:00:00Z',
      fin: '2026-11-20T09:30:00Z',
      motivo: 'Consulta general',
      estado: 'confirmado',
      origen: 'online',
    };
    vi.mocked(receptionService.updateTurnoEstado).mockResolvedValueOnce(updatedTurno);

    const { wrapper, invalidateSpy } = createWrapper();
    const { result } = renderHook(() => useUpdateTurnoEstadoMutation(), { wrapper });

    result.current.mutate({ turnoId: 1, estado: 'confirmado' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.updateTurnoEstado).toHaveBeenCalledWith(1, {
      estado: 'confirmado',
    });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['agenda-dia'] });
  });
});
