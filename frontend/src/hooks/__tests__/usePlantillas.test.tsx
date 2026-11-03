import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  usePlantillasQuery,
  useCreatePlantillaMutation,
  useUpdatePlantillaMutation,
  useDeletePlantillaMutation,
} from '@/hooks/usePlantillas';
import * as receptionService from '@/services/reception.service';
import type { PlantillaItem } from '@/types/reception';

vi.mock('@/services/reception.service', () => ({
  getPlantillas: vi.fn(),
  createPlantilla: vi.fn(),
  updatePlantilla: vi.fn(),
  deletePlantilla: vi.fn(),
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

describe('usePlantillas hooks (Strict TDD - C-14 / Hard Rule #6)', () => {
  const samplePlantilla: PlantillaItem = {
    id: 5,
    odontologo_id: 2,
    dia_semana: 0,
    hora_inicio: '08:00:00',
    hora_fin: '12:00:00',
    duracion_slot_minutos: 30,
    prestacion: 'Consulta general',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('usePlantillasQuery fetches availability templates filtered by optional odontologoId', async () => {
    vi.mocked(receptionService.getPlantillas).mockResolvedValueOnce([samplePlantilla]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => usePlantillasQuery(2), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.getPlantillas).toHaveBeenCalledWith(2);
    expect(result.current.data).toEqual([samplePlantilla]);
  });

  it('useCreatePlantillaMutation creates a template and invalidates ["plantillas"]', async () => {
    vi.mocked(receptionService.createPlantilla).mockResolvedValueOnce(samplePlantilla);

    const { wrapper, invalidateSpy } = createWrapper();
    const { result } = renderHook(() => useCreatePlantillaMutation(), { wrapper });

    result.current.mutate({
      odontologo_id: 2,
      dia_semana: 0,
      hora_inicio: '08:00',
      hora_fin: '12:00',
      duracion_slot_minutos: 30,
      prestacion: 'Consulta general',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.createPlantilla).toHaveBeenCalled();
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['plantillas'] });
  });

  it('useUpdatePlantillaMutation partially updates a template and invalidates ["plantillas"]', async () => {
    vi.mocked(receptionService.updatePlantilla).mockResolvedValueOnce({
      ...samplePlantilla,
      hora_fin: '13:00:00',
    });

    const { wrapper, invalidateSpy } = createWrapper();
    const { result } = renderHook(() => useUpdatePlantillaMutation(), { wrapper });

    result.current.mutate({
      plantillaId: 5,
      payload: { hora_fin: '13:00' },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.updatePlantilla).toHaveBeenCalledWith(5, {
      hora_fin: '13:00',
    });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['plantillas'] });
  });

  it('useDeletePlantillaMutation deletes a template and invalidates ["plantillas"]', async () => {
    vi.mocked(receptionService.deletePlantilla).mockResolvedValueOnce(undefined);

    const { wrapper, invalidateSpy } = createWrapper();
    const { result } = renderHook(() => useDeletePlantillaMutation(), { wrapper });

    result.current.mutate(5);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receptionService.deletePlantilla).toHaveBeenCalledWith(5);
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['plantillas'] });
  });
});
