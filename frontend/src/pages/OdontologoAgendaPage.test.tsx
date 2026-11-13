import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OdontologoAgendaPage } from '@/pages/OdontologoAgendaPage';
import * as dentistService from '@/services/dentist.service';
import type { MisTurnosOdontologoItem } from '@/types/dentist';

vi.mock('@/services/dentist.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/dentist.service')>();
  return {
    ...actual,
    getMisTurnosOdontologo: vi.fn(),
    getMisTurnosCalendario: vi.fn(),
    updateTurnoAsistencia: vi.fn(),
  };
});

function renderWithQueryClient(ui: React.ReactElement, initialRoute = '/odontologo/agenda') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const SYNTHETIC_DENTIST_TURNOS: MisTurnosOdontologoItem[] = [
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
  {
    // CB-01: Contiguous appointment where fin_A (09:30) == inicio_B (09:30)
    id: 502,
    paciente_id: 21,
    odontologo_id: 7,
    inicio: '2026-11-10T09:30:00Z',
    fin: '2026-11-10T10:00:00Z',
    motivo: 'Limpieza dental',
    estado: 'solicitado',
    origen: 'recepcion',
    paciente: {
      id: 21,
      nombre: 'Mateo Fernández',
      nro_socio: 'SOC-1002',
      email: 'mateo.fernandez@example.com',
    },
  },
  {
    id: 503,
    paciente_id: 22,
    odontologo_id: 7,
    inicio: '2026-11-10T10:30:00Z',
    fin: '2026-11-10T11:00:00Z',
    motivo: 'Extracción simple',
    estado: 'presente',
    origen: 'online',
    paciente: {
      id: 22,
      nombre: 'Valentina Torres',
      nro_socio: 'SOC-1003',
      email: 'valentina.torres@example.com',
    },
  },
  {
    id: 504,
    paciente_id: 23,
    odontologo_id: 7,
    inicio: '2026-11-10T11:00:00Z',
    fin: '2026-11-10T11:30:00Z',
    motivo: 'Endodoncia',
    estado: 'cancelado',
    origen: 'online',
    paciente: {
      id: 23,
      nombre: 'Santiago Díaz',
      nro_socio: null,
      email: null,
    },
  },
];

describe('OdontologoAgendaPage (Strict TDD - US-007 & US-008 / C-15)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(dentistService.getMisTurnosCalendario).mockResolvedValue({
      anio: 2026,
      mes: 11,
      dias: [],
    });
  });

  it('renders chronological daily self-agenda, contiguous slots (CB-01), and restricts Presente/Ausente buttons strictly to confirmado state (RN-TU-03)', async () => {
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValueOnce(
      SYNTHETIC_DENTIST_TURNOS
    );

    renderWithQueryClient(<OdontologoAgendaPage initialFecha="2026-11-10" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    expect(dentistService.getMisTurnosOdontologo).toHaveBeenCalledWith(
      '2026-11-10'
    );

    // CB-01: Contiguous slots 09:00 – 09:30 and 09:30 – 10:00 rendered sequentially in order
    const row501 = screen.getByTestId('dentist-agenda-row-501');
    const row502 = screen.getByTestId('dentist-agenda-row-502');
    expect(within(row501).getByText(/09:00\s*–\s*09:30/)).toBeInTheDocument();
    expect(within(row502).getByText(/09:30\s*–\s*10:00/)).toBeInTheDocument();
    expect(within(row501).getByText(/SOC-1001/i)).toBeInTheDocument();

    // Row 501 (confirmado) exposes Presente & Ausente buttons
    expect(
      within(row501).getByRole('button', { name: /presente/i })
    ).toBeEnabled();
    expect(
      within(row501).getByRole('button', { name: /ausente/i })
    ).toBeEnabled();

    // Row 502 (solicitado), Row 503 (presente), Row 504 (cancelado) DO NOT expose Presente or Ausente buttons
    for (const nonConfirmadoId of [502, 503, 504]) {
      const row = screen.getByTestId(`dentist-agenda-row-${nonConfirmadoId}`);
      expect(
        within(row).queryByRole('button', { name: /presente/i })
      ).not.toBeInTheDocument();
      expect(
        within(row).queryByRole('button', { name: /ausente/i })
      ).not.toBeInTheDocument();
    }
  });

  it('renders clean empty state when the selected date has no appointments', async () => {
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValueOnce([]);

    renderWithQueryClient(<OdontologoAgendaPage initialFecha="2026-11-12" />);

    await waitFor(() => {
      expect(
        screen.getByText(/no tenés turnos programados para la fecha seleccionada/i)
      ).toBeInTheDocument();
    });

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('marks a confirmado appointment as presente via PATCH /api/turnos/{id} and shows confirmation status', async () => {
    const user = userEvent.setup();
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValue(
      SYNTHETIC_DENTIST_TURNOS
    );
    vi.mocked(dentistService.updateTurnoAsistencia).mockResolvedValueOnce({
      id: 501,
      paciente_id: 20,
      odontologo_id: 7,
      inicio: '2026-11-10T09:00:00Z',
      fin: '2026-11-10T09:30:00Z',
      motivo: 'Control general',
      estado: 'presente',
      origen: 'online',
    });

    renderWithQueryClient(<OdontologoAgendaPage initialFecha="2026-11-10" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const row501 = screen.getByTestId('dentist-agenda-row-501');
    await user.click(within(row501).getByRole('button', { name: /presente/i }));

    await waitFor(() => {
      expect(dentistService.updateTurnoAsistencia).toHaveBeenCalledWith(501, {
        estado: 'presente',
      });
    });

    const statusBanner = await screen.findByRole('status');
    expect(statusBanner).toHaveTextContent(
      /asistencia de lucía gómez registrada como presente/i
    );
  });

  it('marks a confirmado appointment as ausente via PATCH /api/turnos/{id}', async () => {
    const user = userEvent.setup();
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValue(
      SYNTHETIC_DENTIST_TURNOS
    );
    vi.mocked(dentistService.updateTurnoAsistencia).mockResolvedValueOnce({
      id: 501,
      paciente_id: 20,
      odontologo_id: 7,
      inicio: '2026-11-10T09:00:00Z',
      fin: '2026-11-10T09:30:00Z',
      motivo: 'Control general',
      estado: 'ausente',
      origen: 'online',
    });

    renderWithQueryClient(<OdontologoAgendaPage initialFecha="2026-11-10" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const row501 = screen.getByTestId('dentist-agenda-row-501');
    await user.click(within(row501).getByRole('button', { name: /ausente/i }));

    await waitFor(() => {
      expect(dentistService.updateTurnoAsistencia).toHaveBeenCalledWith(501, {
        estado: 'ausente',
      });
    });
  });

  it('surfaces accessible error alert (role="alert") when PATCH /api/turnos/{id} returns 409 Conflict or 403 Forbidden', async () => {
    const user = userEvent.setup();
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValue(
      SYNTHETIC_DENTIST_TURNOS
    );
    vi.mocked(dentistService.updateTurnoAsistencia).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          detail: 'Solo se puede registrar asistencia sobre turnos confirmados.',
        },
      },
    });

    renderWithQueryClient(<OdontologoAgendaPage initialFecha="2026-11-10" />);

    await waitFor(() => {
      expect(screen.getByText('Lucía Gómez')).toBeInTheDocument();
    });

    const row501 = screen.getByTestId('dentist-agenda-row-501');
    await user.click(within(row501).getByRole('button', { name: /presente/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(
      /solo se puede registrar asistencia sobre turnos confirmados/i
    );
  });

  it('displays Calendario de Confirmados view, month navigation, and lists only reception-confirmed appointments', async () => {
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValue(
      SYNTHETIC_DENTIST_TURNOS
    );

    renderWithQueryClient(
      <OdontologoAgendaPage initialFecha="2026-11-10" initialVista="calendario" />,
      '/odontologo/calendario'
    );

    // Verify calendar view header and month navigation
    expect(await screen.findByText(/Calendario de Turnos Confirmados/i)).toBeInTheDocument();
    expect(screen.getByText(/Navegación Mensual/i)).toBeInTheDocument();

    // Verify confirmed patient card is rendered (Turno 501: Lucía Gómez)
    expect(await screen.findByTestId('confirmed-card-501')).toBeInTheDocument();
    expect(
      within(screen.getByTestId('confirmed-card-501')).getByText('Confirmado por Recepción')
    ).toBeInTheDocument();

    // Verify non-confirmed appointments (e.g. Turno 502: Mateo Fernández, 'solicitado') are NOT in this view
    expect(screen.queryByTestId('confirmed-card-502')).not.toBeInTheDocument();
  });

  it('renders status dots only on days with appointments and queries next month on navigation (C-22)', async () => {
    const user = userEvent.setup();
    vi.mocked(dentistService.getMisTurnosOdontologo).mockResolvedValue([]);
    vi.mocked(dentistService.getMisTurnosCalendario).mockResolvedValue({
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
        {
          fecha: '2026-11-16',
          confirmados: 0,
          solicitados: 1,
          atendidos: 0,
          total_activos: 1,
        },
      ],
    });

    renderWithQueryClient(
      <OdontologoAgendaPage initialFecha="2026-11-10" initialVista="calendario" />,
      '/odontologo/calendario'
    );

    expect(await screen.findByTestId('calendar-dot-confirmados-2026-11-13')).toBeInTheDocument();
    expect(screen.getByTestId('calendar-dot-solicitados-2026-11-13')).toBeInTheDocument();
    expect(screen.getByTestId('calendar-dot-solicitados-2026-11-16')).toBeInTheDocument();
    expect(screen.queryByTestId('calendar-dot-confirmados-2026-11-16')).not.toBeInTheDocument();
    expect(screen.queryByTestId('calendar-dot-confirmados-2026-11-15')).not.toBeInTheDocument();
    expect(screen.queryByTestId('calendar-dot-solicitados-2026-11-15')).not.toBeInTheDocument();

    // Legend is visible
    expect(screen.getByText('Confirmados')).toBeInTheDocument();
    expect(screen.getByText('Pend. recepción')).toBeInTheDocument();

    // Navigate to next month (December 2026)
    await user.click(screen.getByRole('button', { name: /mes siguiente/i }));
    await waitFor(() => {
      expect(dentistService.getMisTurnosCalendario).toHaveBeenCalledWith(2026, 12);
    });
  });
});
