import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PacienteMisTurnosPage } from '@/pages/PacienteMisTurnosPage';
import * as patientService from '@/services/patient.service';
import type { MisTurnosPacienteItem } from '@/types/patient';

vi.mock('@/services/patient.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/patient.service')>();
  return {
    ...actual,
    getMisTurnosPaciente: vi.fn(),
    cancelarTurnoPaciente: vi.fn(),
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

const SYNTHETIC_PACIENTE_TURNOS: MisTurnosPacienteItem[] = [
  {
    id: 801,
    paciente_id: 10,
    odontologo_id: 2,
    inicio: '2026-11-25T10:00:00-03:00',
    fin: '2026-11-25T10:30:00-03:00',
    motivo: 'Control general',
    estado: 'solicitado',
    origen: 'online',
    odontologo: {
      id: 2,
      nombre: 'Dr. Martín Ruiz',
      nro_socio: null,
      email: 'martin.ruiz@clinica.com',
    },
  },
  {
    id: 802,
    paciente_id: 10,
    odontologo_id: 3,
    inicio: '2026-11-26T14:00:00-03:00',
    fin: '2026-11-26T14:30:00-03:00',
    motivo: 'Limpieza dental',
    estado: 'confirmado',
    origen: 'recepcion',
    odontologo: {
      id: 3,
      nombre: 'Dra. Sofía Pereyra',
      nro_socio: null,
      email: 'sofia.pereyra@clinica.com',
    },
  },
  {
    id: 803,
    paciente_id: 10,
    odontologo_id: 2,
    inicio: '2026-11-20T09:00:00-03:00',
    fin: '2026-11-20T09:30:00-03:00',
    motivo: 'Consulta previa',
    estado: 'cancelado',
    origen: 'online',
    odontologo: {
      id: 2,
      nombre: 'Dr. Martín Ruiz',
      nro_socio: null,
      email: 'martin.ruiz@clinica.com',
    },
  },
  {
    id: 804,
    paciente_id: 10,
    odontologo_id: 2,
    inicio: '2026-11-18T09:00:00-03:00',
    fin: '2026-11-18T09:30:00-03:00',
    motivo: 'Tratamiento completado',
    estado: 'presente',
    origen: 'recepcion',
    odontologo: {
      id: 2,
      nombre: 'Dr. Martín Ruiz',
      nro_socio: null,
      email: 'martin.ruiz@clinica.com',
    },
  },
];

describe('PacienteMisTurnosPage (Strict TDD - US-004 / C-13)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders patient appointments chronologically with dentist details, badges, and cancellation actions', async () => {
    vi.mocked(patientService.getMisTurnosPaciente).mockResolvedValueOnce(
      SYNTHETIC_PACIENTE_TURNOS
    );

    renderWithQueryClient(<PacienteMisTurnosPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Dr. Martín Ruiz').length).toBeGreaterThan(0);
    });

    expect(patientService.getMisTurnosPaciente).toHaveBeenCalledTimes(1);

    // Row 801 (solicitado) exposes Cancelar button
    const row801 = screen.getByTestId('mis-turnos-row-801');
    expect(within(row801).getByText('Control general')).toBeInTheDocument();
    expect(within(row801).getByRole('button', { name: /cancelar turno/i })).toBeEnabled();

    // Row 802 (confirmado) exposes Cancelar button
    const row802 = screen.getByTestId('mis-turnos-row-802');
    expect(within(row802).getByText('Dra. Sofía Pereyra')).toBeInTheDocument();
    expect(within(row802).getByRole('button', { name: /cancelar turno/i })).toBeEnabled();

    // Rows 803 (cancelado) and 804 (presente) DO NOT expose cancel button
    const row803 = screen.getByTestId('mis-turnos-row-803');
    expect(within(row803).queryByRole('button', { name: /cancelar turno/i })).not.toBeInTheDocument();
    expect(within(row803).getByText('Cancelado')).toBeInTheDocument();

    const row804 = screen.getByTestId('mis-turnos-row-804');
    expect(within(row804).queryByRole('button', { name: /cancelar turno/i })).not.toBeInTheDocument();
    expect(within(row804).getByText('Presente')).toBeInTheDocument();
  });

  it('filters appointments when user changes fecha_desde and fecha_hasta', async () => {
    const user = userEvent.setup();
    vi.mocked(patientService.getMisTurnosPaciente).mockResolvedValue(
      SYNTHETIC_PACIENTE_TURNOS
    );

    renderWithQueryClient(<PacienteMisTurnosPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Dr. Martín Ruiz').length).toBeGreaterThan(0);
    });

    const fechaDesdeInput = screen.getByLabelText(/fecha desde/i);
    const fechaHastaInput = screen.getByLabelText(/fecha hasta/i);

    await user.clear(fechaDesdeInput);
    await user.type(fechaDesdeInput, '2026-11-25');
    await user.clear(fechaHastaInput);
    await user.type(fechaHastaInput, '2026-11-28');

    await waitFor(() => {
      expect(patientService.getMisTurnosPaciente).toHaveBeenCalledWith({
        fecha_desde: '2026-11-25',
        fecha_hasta: '2026-11-28',
      });
    });
  });

  it('cancels an active appointment via PATCH /api/turnos/{id} with 24h+ anticipation (RN-TU-04)', async () => {
    const user = userEvent.setup();
    vi.mocked(patientService.getMisTurnosPaciente).mockResolvedValue(
      SYNTHETIC_PACIENTE_TURNOS
    );
    vi.mocked(patientService.cancelarTurnoPaciente).mockResolvedValueOnce({
      id: 801,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-25T10:00:00-03:00',
      fin: '2026-11-25T10:30:00-03:00',
      motivo: 'Control general',
      estado: 'cancelado',
      origen: 'online',
    });

    renderWithQueryClient(<PacienteMisTurnosPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Dr. Martín Ruiz').length).toBeGreaterThan(0);
    });

    const row801 = screen.getByTestId('mis-turnos-row-801');
    const cancelBtn = within(row801).getByRole('button', { name: /cancelar turno/i });
    await user.click(cancelBtn);

    await waitFor(() => {
      expect(patientService.cancelarTurnoPaciente).toHaveBeenCalledWith(801);
    });

    const statusBanner = await screen.findByRole('status');
    expect(statusBanner).toHaveTextContent(/turno cancelado correctamente/i);
  });

  it('surfaces accessible error alert (role="alert") when cancellation fails due to < 24h anticipation (RN-TU-05)', async () => {
    const user = userEvent.setup();
    vi.mocked(patientService.getMisTurnosPaciente).mockResolvedValue(
      SYNTHETIC_PACIENTE_TURNOS
    );
    vi.mocked(patientService.cancelarTurnoPaciente).mockRejectedValueOnce({
      response: {
        status: 422,
        data: {
          detail: 'La cancelación o anulación requiere al menos 24 horas de anticipación.',
        },
      },
    });

    renderWithQueryClient(<PacienteMisTurnosPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Dr. Martín Ruiz').length).toBeGreaterThan(0);
    });

    const row801 = screen.getByTestId('mis-turnos-row-801');
    const cancelBtn = within(row801).getByRole('button', { name: /cancelar turno/i });
    await user.click(cancelBtn);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(
      /la cancelación o anulación requiere al menos 24 horas de anticipación/i
    );
  });
});
