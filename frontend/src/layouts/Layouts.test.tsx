import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { AppLayout } from './AppLayout';
import { AuthLayout } from './AuthLayout';
import type { UserProfile } from '@/types/auth';

describe('Layouts Architecture (Strict TDD)', () => {
  describe('AuthLayout', () => {
    it('renders clinic branding and children content', () => {
      render(
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<div>Formulario de Login</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
      expect(screen.getByText(/turnos odontología/i)).toBeInTheDocument();
      expect(screen.getByText(/formulario de login/i)).toBeInTheDocument();
    });
  });

  describe('AppLayout by Role', () => {
    it('renders receptionist navigation with Agenda and Plantillas links', () => {
      const recepcionista: UserProfile = {
        id: 1,
        email: 'recepcion@clinica.com',
        nombre: 'María',
        apellido: 'Lopez',
        rol: 'recepcion',
      };

      render(
        <MemoryRouter initialEntries={['/recepcion/agenda']}>
          <Routes>
            <Route element={<AppLayout user={recepcionista} onLogout={vi.fn()} />}>
              <Route path="/recepcion/agenda" element={<div>Vista Agenda Recepción</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('María Lopez')).toBeInTheDocument();
      expect(screen.getByText('Recepción')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /agenda del día/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /plantillas/i })).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /mi agenda/i })).not.toBeInTheDocument();
    });

    it('renders dentist navigation with Mi agenda link only', () => {
      const odontologo: UserProfile = {
        id: 2,
        email: 'dentist@clinica.com',
        nombre: 'Dr. Carlos',
        apellido: 'Sosa',
        rol: 'odontologo',
      };

      render(
        <MemoryRouter initialEntries={['/odontologo/agenda']}>
          <Routes>
            <Route element={<AppLayout user={odontologo} onLogout={vi.fn()} />}>
              <Route path="/odontologo/agenda" element={<div>Vista Agenda Profesional</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText(/dr\. carlos sosa/i)).toBeInTheDocument();
      expect(screen.getByText(/odontólogo/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /mi agenda/i })).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /plantillas/i })).not.toBeInTheDocument();
    });

    it('renders patient navigation with Buscar turno and Mis turnos links', () => {
      const paciente: UserProfile = {
        id: 3,
        email: 'paciente@gmail.com',
        nombre: 'Lucía',
        apellido: 'Fernandez',
        rol: 'paciente',
      };

      render(
        <MemoryRouter initialEntries={['/paciente/mis-turnos']}>
          <Routes>
            <Route element={<AppLayout user={paciente} onLogout={vi.fn()} />}>
              <Route path="/paciente/mis-turnos" element={<div>Mis Turnos</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText(/lucía fernandez/i)).toBeInTheDocument();
      expect(screen.getByText(/paciente/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /buscar turno/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /mis turnos/i })).toBeInTheDocument();
    });

    it('triggers onLogout when Cerrar sesión button is clicked', async () => {
      const handleLogout = vi.fn();
      const user: UserProfile = {
        id: 1,
        email: 'admin@clinica.com',
        nombre: 'Admin',
        apellido: 'User',
        rol: 'recepcion',
      };

      render(
        <MemoryRouter>
          <AppLayout user={user} onLogout={handleLogout} />
        </MemoryRouter>
      );

      const logoutBtn = screen.getByRole('button', { name: /cerrar sesión/i });
      await userEvent.click(logoutBtn);
      expect(handleLogout).toHaveBeenCalledTimes(1);
    });
  });
});
