import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { DevToolbar } from './DevToolbar';
import { AuthContext, type AuthContextType } from '@/context/AuthContext';
import { router } from '@/router/routes';

function renderDevToolbar(authOverrides?: Partial<AuthContextType>) {
  const defaultAuth: AuthContextType = {
    user: null,
    token: null,
    login: vi.fn(),
    loginAs: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
    updateUser: vi.fn(),
    isLoading: false,
    isAuthenticated: false,
    ...authOverrides,
  };

  return {
    ...render(
      <AuthContext.Provider value={defaultAuth}>
        <DevToolbar />
      </AuthContext.Provider>
    ),
    auth: defaultAuth,
  };
}

describe('DevToolbar Collapsible FAB (Strict TDD)', () => {
  it('renders collapsed floating trigger dot by default', () => {
    renderDevToolbar();

    const triggerBtn = screen.getByRole('button', { name: /abrir simulador de roles/i });
    expect(triggerBtn).toBeInTheDocument();
    // Options should not be visible when collapsed
    expect(screen.queryByText(/simulador c-11/i)).not.toBeInTheDocument();
  });

  it('expands role options on click and collapses on close click', async () => {
    const user = userEvent.setup();
    renderDevToolbar();

    const triggerBtn = screen.getByRole('button', { name: /abrir simulador de roles/i });
    await user.click(triggerBtn);

    // Options are now visible
    expect(screen.getByText(/simulador c-11/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /público \(login\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /recepción/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /odontólogo/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /paciente/i })).toBeInTheDocument();

    // Close button
    const closeBtn = screen.getByRole('button', { name: /cerrar simulador/i });
    await user.click(closeBtn);

    expect(screen.queryByText(/simulador c-11/i)).not.toBeInTheDocument();
  });

  it('switches role and triggers loginAs when a role is clicked', async () => {
    const user = userEvent.setup();
    const loginAsSpy = vi.fn();
    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve());

    renderDevToolbar({ loginAs: loginAsSpy });

    const triggerBtn = screen.getByRole('button', { name: /abrir simulador de roles/i });
    await user.click(triggerBtn);

    const recepBtn = screen.getByRole('button', { name: /recepción/i });
    await user.click(recepBtn);

    expect(loginAsSpy).toHaveBeenCalledWith('recepcion');
    expect(navigateSpy).toHaveBeenCalledWith('/recepcion/agenda');
  });
});
