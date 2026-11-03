import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '@/lib/api';
import {
  getAgendaDia,
  updateTurnoEstado,
  getPlantillas,
  createPlantilla,
  updatePlantilla,
  deletePlantilla,
  formatLocalDateISO,
  normalizeTimeHHMM,
} from '@/services/reception.service';
import type {
  AgendaTurnoDiaItem,
  PlantillaItem,
  TurnoResponseItem,
} from '@/types/reception';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('reception.service (Strict TDD - C-14)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAgendaDia (GET /api/agenda/dia)', () => {
    it('calls GET /agenda/dia with required fecha and omits odontologo_id when not provided', async () => {
      const mockData: AgendaTurnoDiaItem[] = [
        {
          id: 101,
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
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData });

      const result = await getAgendaDia({ fecha: '2026-11-20' });

      expect(apiClient.get).toHaveBeenCalledWith('/agenda/dia', {
        params: { fecha: '2026-11-20' },
      });
      expect(result).toEqual(mockData);
    });

    it('includes odontologo_id query parameter when provided', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] });

      await getAgendaDia({ fecha: '2026-11-20', odontologo_id: 2 });

      expect(apiClient.get).toHaveBeenCalledWith('/agenda/dia', {
        params: { fecha: '2026-11-20', odontologo_id: 2 },
      });
    });
  });

  describe('updateTurnoEstado (PATCH /api/turnos/{id} - Hard Rules #1, #8, #9)', () => {
    it('sends PATCH /turnos/{id} with exact { estado: "confirmado" } payload and no extra fields', async () => {
      const mockResponse: TurnoResponseItem = {
        id: 101,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-20T09:00:00Z',
        fin: '2026-11-20T09:30:00Z',
        motivo: 'Consulta general',
        estado: 'confirmado',
        origen: 'online',
      };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

      const result = await updateTurnoEstado(101, { estado: 'confirmado' });

      expect(apiClient.patch).toHaveBeenCalledWith('/turnos/101', {
        estado: 'confirmado',
      });
      expect(result.estado).toBe('confirmado');
    });

    it('sends PATCH /turnos/{id} with exact { estado: "anulado" } payload', async () => {
      const mockResponse: TurnoResponseItem = {
        id: 102,
        paciente_id: 10,
        odontologo_id: 2,
        inicio: '2026-11-20T10:00:00Z',
        fin: '2026-11-20T10:30:00Z',
        motivo: 'Control',
        estado: 'anulado',
        origen: 'recepcion',
      };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

      const result = await updateTurnoEstado(102, { estado: 'anulado' });

      expect(apiClient.patch).toHaveBeenCalledWith('/turnos/102', {
        estado: 'anulado',
      });
      expect(result.estado).toBe('anulado');
    });
  });

  describe('Plantillas CRUD (/api/plantillas - US-006)', () => {
    const samplePlantilla: PlantillaItem = {
      id: 1,
      odontologo_id: 2,
      dia_semana: 0,
      hora_inicio: '08:00:00',
      hora_fin: '12:00:00',
      duracion_slot_minutos: 30,
      prestacion: 'Consulta general',
    };

    it('getPlantillas calls GET /plantillas with optional odontologo_id filter', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [samplePlantilla] });

      const all = await getPlantillas();
      expect(apiClient.get).toHaveBeenCalledWith('/plantillas', { params: {} });
      expect(all).toEqual([samplePlantilla]);

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [samplePlantilla] });
      await getPlantillas(2);
      expect(apiClient.get).toHaveBeenCalledWith('/plantillas', {
        params: { odontologo_id: 2 },
      });
    });

    it('createPlantilla sends POST /plantillas with strict extra="forbid" fields', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: samplePlantilla });

      const created = await createPlantilla({
        odontologo_id: 2,
        dia_semana: 0,
        hora_inicio: '08:00',
        hora_fin: '12:00',
        duracion_slot_minutos: 30,
        prestacion: '  Consulta general  ',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/plantillas', {
        odontologo_id: 2,
        dia_semana: 0,
        hora_inicio: '08:00',
        hora_fin: '12:00',
        duracion_slot_minutos: 30,
        prestacion: 'Consulta general',
      });
      expect(created).toEqual(samplePlantilla);
    });

    it('updatePlantilla sends PATCH /plantillas/{id} with only defined mutable fields', async () => {
      vi.mocked(apiClient.patch).mockResolvedValueOnce({
        data: { ...samplePlantilla, hora_fin: '13:00:00', prestacion: 'Endodoncia' },
      });

      const updated = await updatePlantilla(1, {
        hora_fin: '13:00',
        prestacion: ' Endodoncia ',
      });

      expect(apiClient.patch).toHaveBeenCalledWith('/plantillas/1', {
        hora_fin: '13:00',
        prestacion: 'Endodoncia',
      });
      expect(updated.prestacion).toBe('Endodoncia');
    });

    it('deletePlantilla sends DELETE /plantillas/{id}', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: undefined });

      await deletePlantilla(1);

      expect(apiClient.delete).toHaveBeenCalledWith('/plantillas/1');
    });
  });

  describe('Date and Time helpers', () => {
    it('formatLocalDateISO formats a local Date as YYYY-MM-DD without UTC drift', () => {
      const date = new Date(2026, 10, 5, 23, 30, 0); // Nov 5, 2026 23:30 local
      expect(formatLocalDateISO(date)).toBe('2026-11-05');
    });

    it('normalizeTimeHHMM strips seconds from HH:MM:SS strings', () => {
      expect(normalizeTimeHHMM('08:00:00')).toBe('08:00');
      expect(normalizeTimeHHMM('14:30')).toBe('14:30');
    });
  });
});
