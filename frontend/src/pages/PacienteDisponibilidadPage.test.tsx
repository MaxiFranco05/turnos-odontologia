import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PacienteDisponibilidadPage } from '@/pages/PacienteDisponibilidadPage';
import * as patientService from '@/services/patient.service';
import type { SlotDisponibleItem, TurnoResponse } from '@/types/patient';

vi.mock('@/services/patient.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/patient.service')>();
  return {
    ...actual,
    getDisponibilidad: vi.fn(),
    createTurnoOnline: vi.fn(),
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

const SYNTHETIC_SLOTS: SlotDisponibleItem[] = [
  {
    inicio: '2026-11-23T09:00:00-03:00',
    fin: '2026-11-23T09:30:00-03:00',
    odontologo_id: 2,
    prestacion: 'Consulta general',
  },
  {
    // CB-01 contiguous slot (fin_A == inicio_B)
    inicio: '2026-11-23T09:30:00-03:00',
    fin: '2026-11-23T10:00:00-03:00',
    odontologo_id: 2,
    prestacion: 'Consulta general',
  },
  {
    inicio: '2026-11-23T11:00:00-03:00',
    fin: '2026-11-23T11:30:00-03:00',
    odontologo_id: 2,
    prestacion: 'Limpieza dental',
  },
];

describe('PacienteDisponibilidadPage (Strict TDD - US-002 & US-003 / C-13)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('queries and renders available slots including contiguous slots (CB-01) without overlap', async () => {
    vi.mocked(patientService.getDisponibilidad).mockResolvedValueOnce(SYNTHETIC_SLOTS);

    renderWithQueryClient(
      <PacienteDisponibilidadPage initialOdontologoId={2} initialFecha="2026-11-23" />
    );

    await waitFor(() => {
      expect(screen.getByText(/09:00\s*–\s*09:30/)).toBeInTheDocument();
    });

    expect(patientService.getDisponibilidad).toHaveBeenCalledWith({
      odontologo_id: 2,
      fecha: '2026-11-23',
    });

    // CB-01: Both contiguous slots are rendered
    expect(screen.getByText(/09:30\s*–\s*10:00/)).toBeInTheDocument();
    expect(screen.getByText(/11:00\s*–\s*11:30/)).toBeInTheDocument();
    expect(screen.getAllByText('Consulta general')).toHaveLength(2);
  });

  it('renders clean empty state when no slots are available for the selected dentist and date', async () => {
    vi.mocked(patientService.getDisponibilidad).mockResolvedValueOnce([]);

    renderWithQueryClient(
      <PacienteDisponibilidadPage initialOdontologoId={2} initialFecha="2026-11-25" />
    );

    await waitFor(() => {
      expect(
        screen.getByText(/no hay turnos disponibles para la fecha u odontólogo seleccionado/i)
      ).toBeInTheDocument();
    });

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('selects a slot, validates non-empty motivo, and submits POST /api/turnos successfully (US-003)', async () => {
    const user = userEvent.setup();
    vi.mocked(patientService.getDisponibilidad).mockResolvedValue(SYNTHETIC_SLOTS);

    const mockCreatedTurno: TurnoResponse = {
      id: 701,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-23T09:00:00-03:00',
      fin: '2026-11-23T09:30:00-03:00',
      motivo: 'Control anual y limpieza',
      estado: 'solicitado',
      origen: 'online',
    };
    vi.mocked(patientService.createTurnoOnline).mockResolvedValueOnce(mockCreatedTurno);

    renderWithQueryClient(
      <PacienteDisponibilidadPage initialOdontologoId={2} initialFecha="2026-11-23" />
    );

    await waitFor(() => {
      expect(screen.getByText(/09:00\s*–\s*09:30/)).toBeInTheDocument();
    });

    // Click on the first slot's "Reservar" button
    const slotCard = screen.getByTestId('slot-card-0');
    const reservarBtn = within(slotCard).getByRole('button', { name: /reservar/i });
    await user.click(reservarBtn);

    // Modal or booking drawer appears
    const motivoInput = screen.getByLabelText(/motivo de consulta/i);
    const confirmarBtn = screen.getByRole('button', { name: /confirmar solicitud/i });

    // Client-side validation: empty motivo fails
    await user.click(confirmarBtn);
    expect(screen.getByText(/el motivo de consulta es obligatorio/i)).toBeInTheDocument();
    expect(patientService.createTurnoOnline).not.toHaveBeenCalled();

    // Fill valid motivo and submit
    await user.type(motivoInput, 'Control anual y limpieza');
    await user.click(confirmarBtn);

    await waitFor(() => {
      expect(patientService.createTurnoOnline).toHaveBeenCalledWith({
        odontologo_id: 2,
        inicio: '2026-11-23T09:00:00-03:00',
        fin: '2026-11-23T09:30:00-03:00',
        motivo: 'Control anual y limpieza',
      });
    });

    const statusBanner = await screen.findByRole('status');
    expect(statusBanner).toHaveTextContent(/solicitud de turno enviada con éxito/i);
  });

  it('surfaces accessible error alert (role="alert") when reservation encounters HTTP 409 Conflict', async () => {
    const user = userEvent.setup();
    vi.mocked(patientService.getDisponibilidad).mockResolvedValue(SYNTHETIC_SLOTS);
    vi.mocked(patientService.createTurnoOnline).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          detail: 'RN-AG-01: El horario solicitado ya se encuentra ocupado para el odontólogo seleccionado.',
        },
      },
    });

    renderWithQueryClient(
      <PacienteDisponibilidadPage initialOdontologoId={2} initialFecha="2026-11-23" />
    );

    await waitFor(() => {
      expect(screen.getByText(/09:00\s*–\s*09:30/)).toBeInTheDocument();
    });

    const slotCard = screen.getByTestId('slot-card-0');
    await user.click(within(slotCard).getByRole('button', { name: /reservar/i }));

    const motivoInput = screen.getByLabelText(/motivo de consulta/i);
    await user.type(motivoInput, 'Dolor en muela');

    const confirmarBtn = screen.getByRole('button', { name: /confirmar solicitud/i });
    await user.click(confirmarBtn);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/el horario solicitado ya se encuentra ocupado/i);
  });

  it('surfaces accessible error alert (role="alert") when query fails with 422 or 404', async () => {
    vi.mocked(patientService.getDisponibilidad).mockRejectedValueOnce({
      response: {
        status: 422,
        data: {
          detail: 'El usuario especificado no posee el rol de odontólogo.',
        },
      },
    });

    renderWithQueryClient(
      <PacienteDisponibilidadPage initialOdontologoId={99} initialFecha="2026-11-23" />
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/no posee el rol de odontólogo/i);
  });
});
