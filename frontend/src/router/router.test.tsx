import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { ProtectedRoute } from './ProtectedRoute';
import type { UserProfile } from '@/types/auth';

describe('Router & ProtectedRoute (Strict TDD)', () => {
  it('redirects unauthenticated user to /login', () => {
    render(
      <MemoryRouter initialEntries={['/recepcion/agenda']}>
        <Routes>
          <Route path="/login" element={<div>Página de Login</div>} />
          <Route element={<ProtectedRoute user={null} />}>
            <Route path="/recepcion/agenda" element={<div>Agenda Recepción</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/página de login/i)).toBeInTheDocument();
    expect(screen.queryByText(/agenda recepción/i)).not.toBeInTheDocument();
  });

  it('allows access when user has the required role', () => {
    const user: UserProfile = {
      id: 1,
      email: 'rec@clinica.com',
      nombre: 'Valeria',
      apellido: 'Rios',
      rol: 'recepcion',
    };

    render(
      <MemoryRouter initialEntries={['/recepcion/agenda']}>
        <Routes>
          <Route element={<ProtectedRoute user={user} allowedRoles={['recepcion']} />}>
            <Route path="/recepcion/agenda" element={<div>Agenda Recepción Habilitada</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/agenda recepción habilitada/i)).toBeInTheDocument();
  });

  it('redirects user when accessing a route for another role', () => {
    const paciente: UserProfile = {
      id: 5,
      email: 'paciente@gmail.com',
      nombre: 'Martin',
      apellido: 'Gomez',
      rol: 'paciente',
    };

    render(
      <MemoryRouter initialEntries={['/odontologo/agenda']}>
        <Routes>
          <Route path="/paciente/mis-turnos" element={<div>Mis Turnos Paciente</div>} />
          <Route element={<ProtectedRoute user={paciente} allowedRoles={['odontologo']} />}>
            <Route path="/odontologo/agenda" element={<div>Agenda Odontólogo</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/mis turnos paciente/i)).toBeInTheDocument();
    expect(screen.queryByText(/agenda odontólogo/i)).not.toBeInTheDocument();
  });
});
