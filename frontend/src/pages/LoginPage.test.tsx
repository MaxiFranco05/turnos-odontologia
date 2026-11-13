import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/context/AuthContext';
import LoginPage from './LoginPage';
import * as authService from '@/services/authService';
import type { TokenResponsePayload, UserProfile } from '@/types/auth';

function renderLoginPage(options?: {
  initialUser?: UserProfile | null;
  initialEntries?: string[];
}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={options?.initialEntries || ['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/recepcion/agenda" element={<div>Portal Recepción</div>} />
            <Route path="/odontologo/agenda" element={<div>Portal Odontólogo</div>} />
            <Route path="/paciente/mis-turnos" element={<div>Portal Paciente</div>} />
            <Route path="/cambiar-password" element={<div>Pantalla Cambiar Contraseña</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('LoginPage (Strict TDD)', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders form fields with accessible labels and clean clinical layout', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/correo o n\.?º de socio/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^contraseña/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/recordar/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument();
  });

  it('renders demo credential quick access chips and populates form fields on click', async () => {
    const user = userEvent.setup();
    renderLoginPage();

    const recepcionChip = screen.getByRole('button', { name: /demo recepción/i });
    expect(recepcionChip).toBeInTheDocument();

    await user.click(recepcionChip);

    const idInput = screen.getByLabelText(/correo o n\.?º de socio/i) as HTMLInputElement;
    const passInput = screen.getByLabelText(/^contraseña/i) as HTMLInputElement;

    expect(idInput.value).toBe('recepcion@turnosodontologia.com');
    expect(passInput.value).toBe('Admin1234!');
  });

  it('populates quick access password from localStorage override when present', async () => {
    const user = userEvent.setup();
    localStorage.setItem('demo_override_password_recepcion@turnosodontologia.com', 'NuevaPass2026!');
    renderLoginPage();

    const recepcionChip = screen.getByRole('button', { name: /demo recepción/i });
    await user.click(recepcionChip);

    const idInput = screen.getByLabelText(/correo o n\.?º de socio/i) as HTMLInputElement;
    const passInput = screen.getByLabelText(/^contraseña/i) as HTMLInputElement;

    expect(idInput.value).toBe('recepcion@turnosodontologia.com');
    expect(passInput.value).toBe('NuevaPass2026!');
  });

  it('validates empty identifier and password client-side before sending request', async () => {
    const user = userEvent.setup();
    const loginSpy = vi.spyOn(authService, 'loginUser');

    renderLoginPage();

    const submitBtn = screen.getByRole('button', { name: /iniciar sesión/i });
    await user.click(submitBtn);

    expect(loginSpy).not.toHaveBeenCalled();
    expect(screen.getByText(/el identificador es requerido/i)).toBeInTheDocument();
    expect(screen.getByText(/la contraseña es requerida/i)).toBeInTheDocument();
  });

  it('successful login redirects to role portal (/recepcion/agenda) when debe_cambiar_password=false', async () => {
    const user = userEvent.setup();
    const mockToken: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '1', rol: 'recepcion', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'recepcion',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    vi.spyOn(authService, 'loginUser').mockResolvedValueOnce(mockToken);

    renderLoginPage();

    await user.type(screen.getByLabelText(/correo o n\.?º de socio/i), 'recepcion@clinica.com');
    await user.type(screen.getByLabelText(/^contraseña/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(screen.getByText('Portal Recepción')).toBeInTheDocument();
    });
  });

  it('successful login redirects to /cambiar-password when debe_cambiar_password=true', async () => {
    const user = userEvent.setup();
    const mockToken: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '2', rol: 'paciente', debe_cambiar_password: true })) + '.sig',
      token_type: 'bearer',
      rol: 'paciente',
      debe_cambiar_password: true,
      perfil_completo: false,
    };

    vi.spyOn(authService, 'loginUser').mockResolvedValueOnce(mockToken);

    renderLoginPage();

    await user.type(screen.getByLabelText(/correo o n\.?º de socio/i), 'paciente@gmail.com');
    await user.type(screen.getByLabelText(/^contraseña/i), 'TempPassword1');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(screen.getByText('Pantalla Cambiar Contraseña')).toBeInTheDocument();
    });
  });

  it('displays generic error alert "Credenciales inválidas" on HTTP 401 (RN-AU-01)', async () => {
    const user = userEvent.setup();
    const error401 = {
      response: {
        status: 401,
        data: { detail: 'Credenciales inválidas' },
      },
    };
    vi.spyOn(authService, 'loginUser').mockRejectedValueOnce(error401);

    renderLoginPage();

    await user.type(screen.getByLabelText(/correo o n\.?º de socio/i), 'inexistente@clinica.com');
    await user.type(screen.getByLabelText(/^contraseña/i), 'WrongPass123');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(screen.getByText(/credenciales inválidas/i)).toBeInTheDocument();
    });
  });

  it('displays rate-limit warning alert on HTTP 429 Too Many Requests', async () => {
    const user = userEvent.setup();
    const error429 = {
      response: {
        status: 429,
        data: { detail: 'Demasiados intentos fallidos. Intente nuevamente en 60 segundos.' },
      },
    };
    vi.spyOn(authService, 'loginUser').mockRejectedValueOnce(error429);

    renderLoginPage();

    await user.type(screen.getByLabelText(/correo o n\.?º de socio/i), 'carlos@clinica.com');
    await user.type(screen.getByLabelText(/^contraseña/i), 'SpamPass123');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(screen.getByText(/demasiados intentos/i)).toBeInTheDocument();
    });
  });
});
