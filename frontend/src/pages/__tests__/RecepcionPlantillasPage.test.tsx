import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecepcionPlantillasPage } from '@/pages/RecepcionPlantillasPage';
import * as receptionService from '@/services/reception.service';
import type { PlantillaItem } from '@/types/reception';

vi.mock('@/services/reception.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/reception.service')>();
  return {
    ...actual,
    getPlantillas: vi.fn(),
    createPlantilla: vi.fn(),
    updatePlantilla: vi.fn(),
    deletePlantilla: vi.fn(),
  };
});

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

const SYNTHETIC_PLANTILLAS: PlantillaItem[] = [
  {
    id: 10,
    odontologo_id: 2,
    dia_semana: 0, // Lunes
    hora_inicio: '08:00:00',
    hora_fin: '12:00:00',
    duracion_slot_minutos: 30,
    prestacion: 'Consulta general',
  },
  {
    id: 11,
    odontologo_id: 2,
    dia_semana: 2, // Miércoles
    hora_inicio: '14:00:00',
    hora_fin: '18:00:00',
    duracion_slot_minutos: 45,
    prestacion: 'Endodoncia',
  },
];

describe('RecepcionPlantillasPage (Strict TDD - US-006 / C-14)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders weekly availability templates grouped by day with normalized HH:MM times', async () => {
    vi.mocked(receptionService.getPlantillas).mockResolvedValueOnce(SYNTHETIC_PLANTILLAS);

    renderWithQueryClient(<RecepcionPlantillasPage />);

    await waitFor(() => {
      expect(screen.getByText('Consulta general')).toBeInTheDocument();
    });

    expect(receptionService.getPlantillas).toHaveBeenCalledWith(undefined);
    expect(screen.getByText(/08:00 – 12:00/i)).toBeInTheDocument();
    expect(screen.getByText(/14:00 – 18:00/i)).toBeInTheDocument();
    expect(screen.getByText('Endodoncia')).toBeInTheDocument();
  });

  it('creates an adjacent availability template (CB-01 hora_fin == hora_inicio) via POST /api/plantillas', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getPlantillas).mockResolvedValue(SYNTHETIC_PLANTILLAS);
    vi.mocked(receptionService.createPlantilla).mockResolvedValueOnce({
      id: 12,
      odontologo_id: 2,
      dia_semana: 0,
      hora_inicio: '12:00:00',
      hora_fin: '16:00:00',
      duracion_slot_minutos: 30,
      prestacion: 'Ortodoncia',
    });

    renderWithQueryClient(<RecepcionPlantillasPage />);

    await waitFor(() => {
      expect(screen.getByText('Consulta general')).toBeInTheDocument();
    });

    const odontologoInput = screen.getByLabelText(/id del odontólogo/i);
    await user.clear(odontologoInput);
    await user.type(odontologoInput, '2');

    const diaSelect = screen.getByLabelText(/día de la semana/i);
    await user.selectOptions(diaSelect, '0');

    const inicioInput = screen.getByLabelText(/hora de inicio/i);
    await user.clear(inicioInput);
    await user.type(inicioInput, '12:00');

    const finInput = screen.getByLabelText(/hora de fin/i);
    await user.clear(finInput);
    await user.type(finInput, '16:00');

    const duracionInput = screen.getByLabelText(/duración del turno/i);
    await user.clear(duracionInput);
    await user.type(duracionInput, '30');

    const prestacionInput = screen.getByLabelText(/prestación o especialidad/i);
    await user.clear(prestacionInput);
    await user.type(prestacionInput, 'Ortodoncia');

    await user.click(screen.getByRole('button', { name: /guardar plantilla/i }));

    await waitFor(() => {
      expect(receptionService.createPlantilla).toHaveBeenCalledWith({
        odontologo_id: 2,
        dia_semana: 0,
        hora_inicio: '12:00',
        hora_fin: '16:00',
        duracion_slot_minutos: 30,
        prestacion: 'Ortodoncia',
      });
    });
  });

  it('surfaces HTTP 409 overlap conflict (RN-AG-01 / CB-04) in an accessible alert while preserving form inputs', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getPlantillas).mockResolvedValue(SYNTHETIC_PLANTILLAS);
    vi.mocked(receptionService.createPlantilla).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          detail: 'La plantilla se superpone con otro bloque horario del mismo odontólogo.',
        },
      },
    });

    renderWithQueryClient(<RecepcionPlantillasPage />);

    await waitFor(() => {
      expect(screen.getByText('Consulta general')).toBeInTheDocument();
    });

    const odontologoInput = screen.getByLabelText(/id del odontólogo/i);
    await user.clear(odontologoInput);
    await user.type(odontologoInput, '2');

    const inicioInput = screen.getByLabelText(/hora de inicio/i);
    await user.clear(inicioInput);
    await user.type(inicioInput, '10:00');

    const finInput = screen.getByLabelText(/hora de fin/i);
    await user.clear(finInput);
    await user.type(finInput, '14:00');

    const prestacionInput = screen.getByLabelText(/prestación o especialidad/i);
    await user.clear(prestacionInput);
    await user.type(prestacionInput, 'Urgencias');

    await user.click(screen.getByRole('button', { name: /guardar plantilla/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(
      /la plantilla se superpone con otro bloque horario del mismo odontólogo/i
    );
    // Preserves form values so receptionist does not lose input
    expect(prestacionInput).toHaveValue('Urgencias');
  });

  it('partially updates an existing template via PATCH /api/plantillas/{id} (Hard Rule #9) and deletes via DELETE', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getPlantillas).mockResolvedValue(SYNTHETIC_PLANTILLAS);
    vi.mocked(receptionService.updatePlantilla).mockResolvedValueOnce({
      ...SYNTHETIC_PLANTILLAS[0],
      hora_fin: '13:00:00',
      prestacion: 'Consulta general extendida',
    });
    vi.mocked(receptionService.deletePlantilla).mockResolvedValueOnce(undefined);

    renderWithQueryClient(<RecepcionPlantillasPage />);

    await waitFor(() => {
      expect(screen.getByText('Consulta general')).toBeInTheDocument();
    });

    const card10 = screen.getByTestId('plantilla-item-10');
    await user.click(within(card10).getByRole('button', { name: /editar/i }));

    // Form switches to edit mode and populates normalized HH:MM
    const finInput = screen.getByLabelText(/hora de fin/i);
    expect(finInput).toHaveValue('12:00');

    await user.clear(finInput);
    await user.type(finInput, '13:00');

    const prestacionInput = screen.getByLabelText(/prestación o especialidad/i);
    await user.clear(prestacionInput);
    await user.type(prestacionInput, 'Consulta general extendida');

    await user.click(screen.getByRole('button', { name: /actualizar plantilla/i }));

    await waitFor(() => {
      expect(receptionService.updatePlantilla).toHaveBeenCalledWith(10, {
        dia_semana: 0,
        hora_inicio: '08:00',
        hora_fin: '13:00',
        duracion_slot_minutos: 30,
        prestacion: 'Consulta general extendida',
      });
    });

    // Now test DELETE on item 11
    const card11 = screen.getByTestId('plantilla-item-11');
    await user.click(within(card11).getByRole('button', { name: /eliminar/i }));

    await waitFor(() => {
      expect(receptionService.deletePlantilla).toHaveBeenCalledWith(11);
    });
  });
});
