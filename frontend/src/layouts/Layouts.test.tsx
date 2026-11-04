import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { AppLayout } from './AppLayout';
import { AuthLayout } from './AuthLayout';
import { ThemeProvider } from '@/context/ThemeContext';
import type { UserProfile } from '@/types/auth';

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ThemeProvider defaultTheme="light">
      {ui}
    </ThemeProvider>
  );
}

describe('Layouts Architecture (Strict TDD - C-20)', () => {
  describe('AuthLayout', () => {
    it('renders clinic branding, ambient glow container, and children content', () => {
      renderWithProviders(
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
      expect(screen.getAllByRole('switch', { name: /cambiar a modo/i }).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('AppLayout - Floating Glass Capsule (Desktop) & Floating Dock (Mobile)', () => {
    it('renders desktop floating glass capsule and mobile dock for receptionist', () => {
      const recepcionista: UserProfile = {
        id: 1,
        email: 'recepcion@clinica.com',
        nombre: 'María',
        apellido: 'Lopez',
        rol: 'recepcion',
      };

      renderWithProviders(
        <MemoryRouter initialEntries={['/recepcion/agenda']}>
          <Routes>
            <Route element={<AppLayout user={recepcionista} onLogout={vi.fn()} />}>
              <Route path="/recepcion/agenda" element={<div>Vista Agenda Recepción</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify user info and role badge
      expect(screen.getByText('María Lopez')).toBeInTheDocument();
      expect(screen.getAllByText('Recepción').length).toBeGreaterThanOrEqual(1);

      // Verify desktop capsule navigation
      const desktopNav = screen.getByRole('navigation', { name: /navegación principal desktop/i });
      expect(desktopNav).toBeInTheDocument();
      expect(desktopNav).toHaveClass('glass-surface');

      // Verify mobile bottom dock navigation
      const mobileDock = screen.getByRole('navigation', { name: /navegación móvil/i });
      expect(mobileDock).toBeInTheDocument();

      // Verify role-based navigation links
      const agendaLinks = screen.getAllByRole('link', { name: /agenda del día/i });
      expect(agendaLinks.length).toBeGreaterThanOrEqual(1);

      const plantillasLinks = screen.getAllByRole('link', { name: /plantillas/i });
      expect(plantillasLinks.length).toBeGreaterThanOrEqual(1);

      expect(screen.queryByRole('link', { name: /mi agenda/i })).not.toBeInTheDocument();
      expect(screen.getAllByRole('switch', { name: /cambiar a modo/i }).length).toBeGreaterThanOrEqual(1);
    });

    it('renders dentist navigation with Mi agenda in desktop capsule and mobile dock', () => {
      const odontologo: UserProfile = {
        id: 2,
        email: 'dentist@clinica.com',
        nombre: 'Dr. Carlos',
        apellido: 'Sosa',
        rol: 'odontologo',
      };

      renderWithProviders(
        <MemoryRouter initialEntries={['/odontologo/agenda']}>
          <Routes>
            <Route element={<AppLayout user={odontologo} onLogout={vi.fn()} />}>
              <Route path="/odontologo/agenda" element={<div>Vista Agenda Profesional</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText(/dr\. carlos sosa/i)).toBeInTheDocument();
      expect(screen.getAllByText(/odontólogo/i).length).toBeGreaterThanOrEqual(1);

      const agendaLinks = screen.getAllByRole('link', { name: /mi agenda/i });
      expect(agendaLinks.length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByRole('link', { name: /plantillas/i })).not.toBeInTheDocument();
      expect(screen.getAllByRole('switch', { name: /cambiar a modo/i }).length).toBeGreaterThanOrEqual(1);
    });

    it('renders patient navigation with Buscar turno and Mis turnos links', () => {
      const paciente: UserProfile = {
        id: 3,
        email: 'paciente@gmail.com',
        nombre: 'Lucía',
        apellido: 'Fernandez',
        rol: 'paciente',
      };

      renderWithProviders(
        <MemoryRouter initialEntries={['/paciente/mis-turnos']}>
          <Routes>
            <Route element={<AppLayout user={paciente} onLogout={vi.fn()} />}>
              <Route path="/paciente/mis-turnos" element={<div>Mis Turnos</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText(/lucía fernandez/i)).toBeInTheDocument();
      expect(screen.getAllByText(/paciente/i).length).toBeGreaterThanOrEqual(1);

      const buscarLinks = screen.getAllByRole('link', { name: /buscar turno/i });
      expect(buscarLinks.length).toBeGreaterThanOrEqual(1);

      const misTurnosLinks = screen.getAllByRole('link', { name: /mis turnos/i });
      expect(misTurnosLinks.length).toBeGreaterThanOrEqual(1);
    });

    it('triggers onLogout when Cerrar sesión button is clicked in user capsule', async () => {
      const handleLogout = vi.fn();
      const user: UserProfile = {
        id: 1,
        email: 'admin@clinica.com',
        nombre: 'Admin',
        apellido: 'User',
        rol: 'recepcion',
      };

      renderWithProviders(
        <MemoryRouter>
          <AppLayout user={user} onLogout={handleLogout} />
        </MemoryRouter>
      );

      const logoutBtns = screen.getAllByRole('button', { name: /cerrar sesión/i });
      await userEvent.click(logoutBtns[0]);
      expect(handleLogout).toHaveBeenCalledTimes(1);
    });
  });
});
