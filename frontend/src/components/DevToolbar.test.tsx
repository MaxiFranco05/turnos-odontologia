import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DevToolbar } from './DevToolbar';
import { AuthContext, type AuthContextType } from '@/context/AuthContext';
import * as authService from '@/services/authService';
import { router } from '@/router/routes';
import type { TokenResponsePayload } from '@/types/auth';

function renderDevToolbar(authOverrides?: Partial<AuthContextType>) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const defaultAuth: AuthContextType = {
    user: null,
    setUser: vi.fn(),
    establishSession: vi.fn(),
    loginAs: vi.fn(),
    logout: vi.fn(),
    ...authOverrides,
  };

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={defaultAuth}>
          <DevToolbar />
        </AuthContext.Provider>
      </QueryClientProvider>
    ),
    auth: defaultAuth,
    queryClient,
  };
}

describe('DevToolbar Collapsible FAB (Real Demo Login)', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders collapsed floating trigger dot by default', () => {
    renderDevToolbar();

    const triggerBtn = screen.getByRole('button', { name: /abrir simulador de roles/i });
    expect(triggerBtn).toBeInTheDocument();
    expect(screen.queryByText(/cambio rápido de rol/i)).not.toBeInTheDocument();
  });

  it('expands role options on click and collapses on close click', async () => {
    const user = userEvent.setup();
    renderDevToolbar();

    const triggerBtn = screen.getByRole('button', { name: /abrir simulador de roles/i });
    await user.click(triggerBtn);

    expect(screen.getByText(/cambio rápido de rol/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /público \(login\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /recepción/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /odontólogo/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /paciente/i })).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /cerrar simulador/i });
    await user.click(closeBtn);

    expect(screen.queryByText(/cambio rápido de rol/i)).not.toBeInTheDocument();
  });

  it('executes real loginUser with demo credentials and navigates to role portal', async () => {
    const user = userEvent.setup();
    const establishMock = vi.fn();
    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve());
    const mockToken: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '1', rol: 'recepcion', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'recepcion',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    const loginSpy = vi.spyOn(authService, 'loginUser').mockResolvedValueOnce(mockToken);

    renderDevToolbar({ establishSession: establishMock });

    await user.click(screen.getByRole('button', { name: /abrir simulador de roles/i }));
    await user.click(screen.getByRole('button', { name: /recepción/i }));

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        identificador: 'recepcion@turnosodontologia.com',
        password: 'Admin1234!',
      });
      expect(establishMock).toHaveBeenCalledWith(
        mockToken,
        'recepcion@turnosodontologia.com',
        true
      );
      expect(navigateSpy).toHaveBeenCalledWith('/recepcion/agenda');
    });
  });

  it('uses persisted localStorage password override when logging in via toolbar', async () => {
    const user = userEvent.setup();
    localStorage.setItem('demo_override_password_recepcion@turnosodontologia.com', 'NuevaClave2026!');
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve());
    const mockToken: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '1', rol: 'recepcion', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'recepcion',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    const loginSpy = vi.spyOn(authService, 'loginUser').mockResolvedValueOnce(mockToken);

    renderDevToolbar();

    await user.click(screen.getByRole('button', { name: /abrir simulador de roles/i }));
    await user.click(screen.getByRole('button', { name: /recepción/i }));

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({
        identificador: 'recepcion@turnosodontologia.com',
        password: 'NuevaClave2026!',
      });
    });
  });

  it('logs out and navigates to /login when Público is clicked', async () => {
    const user = userEvent.setup();
    const logoutSpy = vi.fn();
    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve());

    renderDevToolbar({ logout: logoutSpy });

    await user.click(screen.getByRole('button', { name: /abrir simulador de roles/i }));
    await user.click(screen.getByRole('button', { name: /público \(login\)/i }));

    expect(logoutSpy).toHaveBeenCalled();
    expect(navigateSpy).toHaveBeenCalledWith('/login');
  });
});
