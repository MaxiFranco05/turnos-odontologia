import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthContext, type AuthContextType } from '@/context/AuthContext';
import CambiarPasswordPage from './CambiarPasswordPage';
import * as authService from '@/services/authService';
import type { TokenResponsePayload, UserProfile } from '@/types/auth';

function renderCambiarPasswordPage(userProfile: UserProfile | null, establishSessionMock = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const authValue: AuthContextType = {
    user: userProfile,
    setUser: vi.fn(),
    establishSession: establishSessionMock,
    loginAs: vi.fn(),
    logout: vi.fn(),
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>
        <MemoryRouter initialEntries={['/cambiar-password']}>
          <Routes>
            <Route path="/cambiar-password" element={<CambiarPasswordPage />} />
            <Route path="/login" element={<div>Pantalla Login</div>} />
            <Route path="/paciente/mis-turnos" element={<div>Portal Paciente</div>} />
            <Route path="/recepcion/agenda" element={<div>Portal Recepción</div>} />
            <Route path="/odontologo/agenda" element={<div>Portal Odontólogo</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe('CambiarPasswordPage (Strict TDD - US-010)', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('redirects to /login if there is no authenticated user', () => {
    renderCambiarPasswordPage(null);
    expect(screen.getByText('Pantalla Login')).toBeInTheDocument();
  });

  it('redirects to role route if user already has debe_cambiar_password=false', () => {
    const userProfile: UserProfile = {
      id: 1,
      email: 'recepcion@clinica.com',
      rol: 'recepcion',
      nombre: 'María',
      apellido: 'López',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    renderCambiarPasswordPage(userProfile);
    expect(screen.getByText('Portal Recepción')).toBeInTheDocument();
  });

  it('renders password fields and hides profile fields when perfil_completo=true', () => {
    const userProfile: UserProfile = {
      id: 2,
      email: 'carlos@clinica.com',
      rol: 'odontologo',
      nombre: 'Carlos',
      apellido: 'Sosa',
      debe_cambiar_password: true,
      perfil_completo: true,
    };

    renderCambiarPasswordPage(userProfile);

    expect(screen.getByLabelText(/contraseña actual/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^nueva contraseña/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar nueva contraseña/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/nombre/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /actualizar contraseña/i })).toBeInTheDocument();
  });

  it('conditionally displays Nombre and Correo electrónico when perfil_completo=false', () => {
    const userProfile: UserProfile = {
      id: 3,
      email: '3@clinica.com',
      rol: 'paciente',
      nombre: 'Paciente',
      apellido: 'Usuario',
      debe_cambiar_password: true,
      perfil_completo: false,
    };

    renderCambiarPasswordPage(userProfile);

    expect(screen.getByLabelText(/^nombre/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument();
  });

  it('validates password strength and confirmation matching before calling API', async () => {
    const user = userEvent.setup();
    const changeSpy = vi.spyOn(authService, 'changePassword');

    const userProfile: UserProfile = {
      id: 3,
      email: 'lucia@gmail.com',
      rol: 'paciente',
      nombre: 'Lucía',
      apellido: 'Fernández',
      debe_cambiar_password: true,
      perfil_completo: true,
    };

    renderCambiarPasswordPage(userProfile);

    const submitBtn = screen.getByRole('button', { name: /actualizar contraseña/i });

    // 1. Empty fields
    await user.click(submitBtn);
    expect(changeSpy).not.toHaveBeenCalled();
    expect(screen.getByText(/la contraseña actual es requerida/i)).toBeInTheDocument();

    // 2. Short password (< 8 chars)
    await user.type(screen.getByLabelText(/contraseña actual/i), 'OldPass123');
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'Short1');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'Short1');
    await user.click(submitBtn);
    expect(changeSpy).not.toHaveBeenCalled();
    expect(screen.getByText(/al menos 8 caracteres/i)).toBeInTheDocument();

    // 3. No uppercase
    await user.clear(screen.getByLabelText(/^nueva contraseña/i));
    await user.clear(screen.getByLabelText(/confirmar nueva contraseña/i));
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'lowercase123');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'lowercase123');
    await user.click(submitBtn);
    expect(screen.getByText(/al menos una letra mayúscula/i)).toBeInTheDocument();

    // 4. No number
    await user.clear(screen.getByLabelText(/^nueva contraseña/i));
    await user.clear(screen.getByLabelText(/confirmar nueva contraseña/i));
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'NoNumbersHere');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'NoNumbersHere');
    await user.click(submitBtn);
    expect(screen.getByText(/al menos un número/i)).toBeInTheDocument();

    // 5. Same as current password
    await user.clear(screen.getByLabelText(/^nueva contraseña/i));
    await user.clear(screen.getByLabelText(/confirmar nueva contraseña/i));
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'OldPass123');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'OldPass123');
    await user.click(submitBtn);
    expect(screen.getByText(/debe ser distinta a la actual/i)).toBeInTheDocument();

    // 6. Confirmation mismatch
    await user.clear(screen.getByLabelText(/^nueva contraseña/i));
    await user.clear(screen.getByLabelText(/confirmar nueva contraseña/i));
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'ValidPass99');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'Mismatch88');
    await user.click(submitBtn);
    expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument();
  });

  it('successful submission updates session and redirects to role route', async () => {
    const user = userEvent.setup();
    const mockResponse: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '3', rol: 'paciente', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'paciente',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    const changeSpy = vi.spyOn(authService, 'changePassword').mockResolvedValueOnce(mockResponse);
    const establishMock = vi.fn();

    const userProfile: UserProfile = {
      id: 3,
      email: '3@clinica.com',
      rol: 'paciente',
      nombre: '',
      apellido: '',
      debe_cambiar_password: true,
      perfil_completo: false,
    };

    renderCambiarPasswordPage(userProfile, establishMock);

    await user.type(screen.getByLabelText(/contraseña actual/i), 'TempPass1');
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'SuperSecret99');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'SuperSecret99');
    await user.type(screen.getByLabelText(/^nombre/i), 'Lucía Gómez');
    await user.clear(screen.getByLabelText(/correo electrónico/i));
    await user.type(screen.getByLabelText(/correo electrónico/i), 'lucia.gomez@gmail.com');

    await user.click(screen.getByRole('button', { name: /actualizar contraseña/i }));

    await waitFor(() => {
      expect(changeSpy).toHaveBeenCalledWith({
        password_actual: 'TempPass1',
        password_nueva: 'SuperSecret99',
        nombre: 'Lucía Gómez',
        email: 'lucia.gomez@gmail.com',
      });
      expect(establishMock).toHaveBeenCalled();
      expect(screen.getByText('Portal Paciente')).toBeInTheDocument();
    });
  });

  it('persists password override in localStorage when demo account changes password', async () => {
    const user = userEvent.setup();
    const establishMock = vi.fn();
    const mockToken: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '1', rol: 'recepcion', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'recepcion',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    vi.spyOn(authService, 'changePassword').mockResolvedValueOnce(mockToken);

    const userProfile: UserProfile = {
      id: 1,
      email: 'recepcion@turnosodontologia.com',
      rol: 'recepcion',
      nombre: 'Recepción',
      apellido: 'Central',
      debe_cambiar_password: true,
      perfil_completo: true,
    };

    renderCambiarPasswordPage(userProfile, establishMock);

    await user.type(screen.getByLabelText(/contraseña actual/i), 'Admin1234!');
    await user.type(screen.getByLabelText(/^nueva contraseña/i), 'Recepcion2026!');
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), 'Recepcion2026!');
    await user.click(screen.getByRole('button', { name: /actualizar contraseña/i }));

    await waitFor(() => {
      expect(localStorage.getItem('demo_override_password_recepcion@turnosodontologia.com')).toBe('Recepcion2026!');
      expect(screen.getByText('Portal Recepción')).toBeInTheDocument();
    });
  });
});
