import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '@/lib/api';
import {
  getMisTurnosCalendario,
  getMisTurnosOdontologo,
  updateTurnoAsistencia,
} from '@/services/dentist.service';
import type { CalendarioMesResponse, MisTurnosOdontologoItem } from '@/types/dentist';
import type { TurnoResponseItem } from '@/types/reception';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('dentist.service (Strict TDD - C-15)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getMisTurnosOdontologo', () => {
    it('queries GET /mis-turnos with exact { fecha } param and never sends odontologo_id, fecha_desde, or fecha_hasta (RN-AU-02)', async () => {
      const mockItems: MisTurnosOdontologoItem[] = [
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

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockItems });

      const result = await getMisTurnosOdontologo('2026-11-10');

      expect(apiClient.get).toHaveBeenCalledTimes(1);
      expect(apiClient.get).toHaveBeenCalledWith('/mis-turnos', {
        params: { fecha: '2026-11-10' },
      });

      const callParams = (
        vi.mocked(apiClient.get).mock.calls[0]?.[1] as {
          params?: Record<string, unknown>;
        }
      )?.params;
      expect(callParams).toEqual({ fecha: '2026-11-10' });
      expect(callParams).not.toHaveProperty('odontologo_id');
      expect(callParams).not.toHaveProperty('fecha_desde');
      expect(callParams).not.toHaveProperty('fecha_hasta');
      expect(result).toEqual(mockItems);
    });
  });

  describe('updateTurnoAsistencia', () => {
    it('sends PATCH /turnos/{id} with exact { estado: "presente" } payload and strips undeclared fields (Hard Rules #1, #8, #9)', async () => {
      const mockResponse: TurnoResponseItem = {
        id: 501,
        paciente_id: 20,
        odontologo_id: 7,
        inicio: '2026-11-10T09:00:00Z',
        fin: '2026-11-10T09:30:00Z',
        motivo: 'Control general',
        estado: 'presente',
        origen: 'online',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

      // Simulate runtime object with extra property to ensure strict stripping
      const rawPayload = {
        estado: 'presente' as const,
        extraField: 'should-be-stripped',
      };

      const result = await updateTurnoAsistencia(501, rawPayload);

      expect(apiClient.patch).toHaveBeenCalledTimes(1);
      expect(apiClient.patch).toHaveBeenCalledWith('/turnos/501', {
        estado: 'presente',
      });
      expect(result).toEqual(mockResponse);
    });

    it('sends PATCH /turnos/{id} with exact { estado: "ausente" } payload', async () => {
      const mockResponse: TurnoResponseItem = {
        id: 502,
        paciente_id: 21,
        odontologo_id: 7,
        inicio: '2026-11-10T09:30:00Z',
        fin: '2026-11-10T10:00:00Z',
        motivo: 'Limpieza dental',
        estado: 'ausente',
        origen: 'recepcion',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

      const result = await updateTurnoAsistencia(502, { estado: 'ausente' });

      expect(apiClient.patch).toHaveBeenCalledWith('/turnos/502', {
        estado: 'ausente',
      });
      expect(result.estado).toBe('ausente');
    });
  });

  describe('getMisTurnosCalendario', () => {
    it('queries GET /mis-turnos/calendario with exact { anio, mes } params (C-22)', async () => {
      const mockCalendar: CalendarioMesResponse = {
        anio: 2026,
        mes: 11,
        dias: [
          {
            fecha: '2026-11-13',
            confirmados: 2,
            solicitados: 1,
            atendidos: 0,
            total_activos: 3,
          },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockCalendar });

      const result = await getMisTurnosCalendario(2026, 11);

      expect(apiClient.get).toHaveBeenCalledTimes(1);
      expect(apiClient.get).toHaveBeenCalledWith('/mis-turnos/calendario', {
        params: { anio: 2026, mes: 11 },
      });
      expect(result).toEqual(mockCalendar);
    });
  });
});
