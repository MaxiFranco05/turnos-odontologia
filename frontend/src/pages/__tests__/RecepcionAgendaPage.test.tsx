import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecepcionAgendaPage } from '@/pages/RecepcionAgendaPage';
import * as receptionService from '@/services/reception.service';
import type { AgendaTurnoDiaItem } from '@/types/reception';

vi.mock('@/services/reception.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/reception.service')>();
  return {
    ...actual,
    getAgendaDia: vi.fn(),
    updateTurnoEstado: vi.fn(),
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

const SYNTHETIC_AGENDA_ITEMS: AgendaTurnoDiaItem[] = [
  {
    id: 201,
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
  {
    id: 202,
    paciente_id: 11,
    odontologo_id: 2,
    inicio: '2026-11-20T10:00:00Z',
    fin: '2026-11-20T10:30:00Z',
    motivo: 'Limpieza dental',
    estado: 'confirmado',
    origen: 'recepcion',
    paciente: {
      id: 11,
      nombre: 'Mateo Fernández',
      nro_socio: 'SOC-1002',
      email: 'mateo.fernandez@example.com',
    },
    odontologo: {
      id: 2,
      nombre: 'Dr. Martín Ruiz',
      email: 'martin.ruiz@clinica.com',
    },
  },
  {
    id: 203,
    paciente_id: 12,
    odontologo_id: 3,
    inicio: '2026-11-20T11:00:00Z',
    fin: '2026-11-20T11:30:00Z',
    motivo: 'Control de ortodoncia',
    estado: 'cancelado',
    origen: 'online',
    paciente: {
      id: 12,
      nombre: 'Valentina Torres',
      nro_socio: 'SOC-1003',
      email: 'valentina.torres@example.com',
    },
    odontologo: {
      id: 3,
      nombre: 'Dra. Sofía Pereyra',
      email: 'sofia.pereyra@clinica.com',
    },
  },
];

describe('RecepcionAgendaPage (Strict TDD - US-005 / C-14)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders daily agenda items including patient cancellations (CB-03) and online origin badges', async () => {
    vi.mocked(receptionService.getAgendaDia).mockResolvedValueOnce(SYNTHETIC_AGENDA_ITEMS);

    renderWithQueryClient(<RecepcionAgendaPage initialFecha="2026-11-20" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    expect(receptionService.getAgendaDia).toHaveBeenCalledWith({
      fecha: '2026-11-20',
      odontologo_id: undefined,
    });

    // Verifies participant details and origin/status badges
    expect(screen.getByText(/SOC-1001/i)).toBeInTheDocument();
    expect(screen.getByText('Mateo Fernández')).toBeInTheDocument();
    expect(screen.getByText('Valentina Torres')).toBeInTheDocument();

    // Row 201 (solicitado) has both Confirmar and Anular enabled
    const rowSolicitado = screen.getByTestId('agenda-row-201');
    expect(within(rowSolicitado).getByRole('button', { name: /confirmar/i })).toBeEnabled();
    expect(within(rowSolicitado).getByRole('button', { name: /anular/i })).toBeEnabled();

    // Row 202 (confirmado) has Anular enabled, but Confirmar is not enabled/rendered
    const rowConfirmado = screen.getByTestId('agenda-row-202');
    expect(within(rowConfirmado).queryByRole('button', { name: /confirmar/i })).not.toBeInTheDocument();
    expect(within(rowConfirmado).getByRole('button', { name: /anular/i })).toBeEnabled();

    // Row 203 (cancelado, origen=online — CB-03) remains visible with Cancelado & Online badges and no mutation buttons
    const rowCancelado = screen.getByTestId('agenda-row-203');
    expect(within(rowCancelado).getByText('Cancelado')).toBeInTheDocument();
    expect(within(rowCancelado).getByText('Online')).toBeInTheDocument();
    expect(within(rowCancelado).queryByRole('button', { name: /confirmar/i })).not.toBeInTheDocument();
    expect(within(rowCancelado).queryByRole('button', { name: /anular/i })).not.toBeInTheDocument();
  });

  it('filters daily agenda by fecha and odontologo_id when user applies dentist filter', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getAgendaDia).mockResolvedValue(SYNTHETIC_AGENDA_ITEMS);

    renderWithQueryClient(<RecepcionAgendaPage initialFecha="2026-11-20" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const odontologoInput = screen.getByLabelText(/filtrar por id de odontólogo/i);
    await user.clear(odontologoInput);
    await user.type(odontologoInput, '2');

    await waitFor(() => {
      expect(receptionService.getAgendaDia).toHaveBeenCalledWith({
        fecha: '2026-11-20',
        odontologo_id: 2,
      });
    });
  });

  it('confirms a solicitado appointment via PATCH /api/turnos/{id} with { estado: "confirmado" }', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getAgendaDia).mockResolvedValue(SYNTHETIC_AGENDA_ITEMS);
    vi.mocked(receptionService.updateTurnoEstado).mockResolvedValueOnce({
      id: 201,
      paciente_id: 10,
      odontologo_id: 2,
      inicio: '2026-11-20T09:00:00Z',
      fin: '2026-11-20T09:30:00Z',
      motivo: 'Consulta general',
      estado: 'confirmado',
      origen: 'online',
    });

    renderWithQueryClient(<RecepcionAgendaPage initialFecha="2026-11-20" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const rowSolicitado = screen.getByTestId('agenda-row-201');
    await user.click(within(rowSolicitado).getByRole('button', { name: /confirmar/i }));

    await waitFor(() => {
      expect(receptionService.updateTurnoEstado).toHaveBeenCalledWith(201, {
        estado: 'confirmado',
      });
    });
  });

  it('annuls an appointment via PATCH /api/turnos/{id} with { estado: "anulado" } and surfaces 422 anticipation error (RN-TU-05)', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getAgendaDia).mockResolvedValue(SYNTHETIC_AGENDA_ITEMS);
    vi.mocked(receptionService.updateTurnoEstado).mockRejectedValueOnce({
      response: {
        status: 422,
        data: {
          detail: 'La cancelación o anulación requiere al menos 24 horas de anticipación.',
        },
      },
    });

    renderWithQueryClient(<RecepcionAgendaPage initialFecha="2026-11-20" />);

    await waitFor(() => {
      expect(screen.getByText('Mateo Fernández')).toBeInTheDocument();
    });

    const rowConfirmado = screen.getByTestId('agenda-row-202');
    await user.click(within(rowConfirmado).getByRole('button', { name: /anular/i }));

    await waitFor(() => {
      expect(receptionService.updateTurnoEstado).toHaveBeenCalledWith(202, {
        estado: 'anulado',
      });
    });

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(
      /la cancelación o anulación requiere al menos 24 horas de anticipación/i
    );
  });

  it('surfaces 422/404 dentist filter error (CB-06) and allows resetting the filter', async () => {
    const user = userEvent.setup();
    vi.mocked(receptionService.getAgendaDia).mockImplementation(async ({ odontologo_id }) => {
      if (odontologo_id === 99) {
        throw {
          response: {
            status: 422,
            data: {
              detail: 'El usuario indicado no posee rol odontologo',
            },
          },
        };
      }
      return SYNTHETIC_AGENDA_ITEMS;
    });

    renderWithQueryClient(<RecepcionAgendaPage initialFecha="2026-11-20" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const odontologoInput = screen.getByLabelText(/filtrar por id de odontólogo/i);
    await user.clear(odontologoInput);
    await user.type(odontologoInput, '99');

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/el usuario indicado no posee rol odontologo/i);

    const resetBtn = screen.getByRole('button', { name: /limpiar filtro/i });
    await user.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });
  });
});
