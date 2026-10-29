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

  it('redirects authenticated user with debe_cambiar_password=true to /cambiar-password', () => {
    const tempUser: UserProfile = {
      id: 9,
      email: 'temp.paciente@example.com',
      nombre: 'Lucia',
      apellido: 'Perez',
      rol: 'paciente',
      debe_cambiar_password: true,
      perfil_completo: false,
    };

    render(
      <MemoryRouter initialEntries={['/paciente/mis-turnos']}>
        <Routes>
          <Route path="/cambiar-password" element={<div>Pantalla Cambiar Contraseña</div>} />
          <Route element={<ProtectedRoute user={tempUser} allowedRoles={['paciente']} />}>
            <Route path="/paciente/mis-turnos" element={<div>Mis Turnos Paciente</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/pantalla cambiar contraseña/i)).toBeInTheDocument();
    expect(screen.queryByText(/mis turnos paciente/i)).not.toBeInTheDocument();
  });

  it('allows access to protected route when debe_cambiar_password=false', () => {
    const activeUser: UserProfile = {
      id: 10,
      email: 'activo.paciente@example.com',
      nombre: 'Carlos',
      apellido: 'Sosa',
      rol: 'paciente',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    render(
      <MemoryRouter initialEntries={['/paciente/mis-turnos']}>
        <Routes>
          <Route path="/cambiar-password" element={<div>Pantalla Cambiar Contraseña</div>} />
          <Route element={<ProtectedRoute user={activeUser} allowedRoles={['paciente']} />}>
            <Route path="/paciente/mis-turnos" element={<div>Mis Turnos Paciente</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/mis turnos paciente/i)).toBeInTheDocument();
    expect(screen.queryByText(/pantalla cambiar contraseña/i)).not.toBeInTheDocument();
  });
});
