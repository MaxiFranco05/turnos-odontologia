import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '@/lib/api';
import {
  getDisponibilidad,
  createTurnoOnline,
  getMisTurnosPaciente,
  cancelarTurnoPaciente,
} from '@/services/patient.service';
import type {
  SlotDisponibleItem,
  TurnoCreatePayload,
  MisTurnosPacienteItem,
  TurnoResponse,
} from '@/types/patient';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('patient.service (Strict TDD - C-13)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDisponibilidad', () => {
    it('queries GET /disponibilidad with exact odontologo_id and fecha parameters (US-002)', async () => {
      const mockSlots: SlotDisponibleItem[] = [
        {
          inicio: '2026-11-23T09:00:00-03:00',
          fin: '2026-11-23T09:30:00-03:00',
          odontologo_id: 2,
          prestacion: 'Consulta general',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockSlots });

      const result = await getDisponibilidad({
        odontologo_id: 2,
        fecha: '2026-11-23',
      });

      expect(apiClient.get).toHaveBeenCalledTimes(1);
      expect(apiClient.get).toHaveBeenCalledWith('/disponibilidad', {
        params: { odontologo_id: 2, fecha: '2026-11-23' },
      });
      expect(result).toEqual(mockSlots);
    });
  });

  describe('createTurnoOnline', () => {
    it('sends POST /turnos with strictly allowed properties omitting paciente_id, estado, and origen (Hard Rules #1, #8, US-003)', async () => {
      const mockCreated: TurnoResponse = {
        id: 301,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual y limpieza',
        estado: 'solicitado',
        origen: 'online',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockCreated });

      // Raw payload with undeclared fields to ensure runtime strictness
      const rawPayload = {
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual y limpieza',
        paciente_id: 999, // Should be omitted
        estado: 'confirmado', // Should be omitted
      };

      const result = await createTurnoOnline(rawPayload as TurnoCreatePayload);

      expect(apiClient.post).toHaveBeenCalledTimes(1);
      expect(apiClient.post).toHaveBeenCalledWith('/turnos', {
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual y limpieza',
      });
      expect(result).toEqual(mockCreated);
    });
  });

  describe('getMisTurnosPaciente', () => {
    it('queries GET /mis-turnos with optional date range and never sends fecha (US-004, RN-AU-02)', async () => {
      const mockItems: MisTurnosPacienteItem[] = [
        {
          id: 301,
          paciente_id: 10,
          odontologo_id: 2,
          inicio: '2026-11-23T09:00:00-03:00',
          fin: '2026-11-23T09:30:00-03:00',
          motivo: 'Control anual y limpieza',
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

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockItems });

      const result = await getMisTurnosPaciente({
        fecha_desde: '2026-11-20',
        fecha_hasta: '2026-11-30',
      });

      expect(apiClient.get).toHaveBeenCalledWith('/mis-turnos', {
        params: {
          fecha_desde: '2026-11-20',
          fecha_hasta: '2026-11-30',
        },
      });

      const params = (
        vi.mocked(apiClient.get).mock.calls[0]?.[1] as {
          params?: Record<string, unknown>;
        }
      )?.params;
      expect(params).not.toHaveProperty('fecha');
      expect(result).toEqual(mockItems);
    });

    it('queries GET /mis-turnos without params when no range is provided', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] });

      const result = await getMisTurnosPaciente();

      expect(apiClient.get).toHaveBeenCalledWith('/mis-turnos', {
        params: {},
      });
      expect(result).toEqual([]);
    });
  });

  describe('cancelarTurnoPaciente', () => {
    it('sends PATCH /turnos/{id} with exact { estado: "cancelado" } payload (RN-TU-04, Hard Rules #1, #9)', async () => {
      const mockResponse: TurnoResponse = {
        id: 301,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual',
        estado: 'cancelado',
        origen: 'online',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

      const result = await cancelarTurnoPaciente(301);

      expect(apiClient.patch).toHaveBeenCalledTimes(1);
      expect(apiClient.patch).toHaveBeenCalledWith('/turnos/301', {
        estado: 'cancelado',
      });
      expect(result.estado).toBe('cancelado');
    });
  });
});
