import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Input } from './Input';

describe('Input component (Strict TDD)', () => {
  it('renders input with label and placeholder', () => {
    render(<Input label="Correo electrónico" placeholder="ejemplo@clinica.com" id="email" />);
    expect(screen.getByLabelText(/correo electrónico/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/ejemplo@clinica.com/i)).toBeInTheDocument();
  });

  it('allows user text input', async () => {
    render(<Input label="Nombre" id="name" />);
    const input = screen.getByLabelText(/nombre/i);
    await userEvent.type(input, 'Dr. Perez');
    expect(input).toHaveValue('Dr. Perez');
  });

  it('renders accessible error state with aria-invalid and aria-describedby', () => {
    render(
      <Input
        label="Contraseña"
        id="password"
        type="password"
        error="La contraseña debe tener al menos 8 caracteres"
      />
    );
    const input = screen.getByLabelText(/contraseña/i);
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'password-error');
    const errorMessage = screen.getByText(/la contraseña debe tener al menos 8 caracteres/i);
    expect(errorMessage).toBeInTheDocument();
    expect(errorMessage).toHaveAttribute('id', 'password-error');
  });

  it('disables input when disabled prop is provided', () => {
    render(<Input label="DNI" id="dni" disabled />);
    expect(screen.getByLabelText(/dni/i)).toBeDisabled();
  });
});
