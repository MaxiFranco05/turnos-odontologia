import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button component (Strict TDD)', () => {
  it('renders button with children text', () => {
    render(<Button>Confirmar Turno</Button>);
    expect(screen.getByRole('button', { name: /confirmar turno/i })).toBeInTheDocument();
  });

  it('triggers onClick handler when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Accionar</Button>);
    await userEvent.click(screen.getByRole('button', { name: /accionar/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not trigger onClick when disabled', async () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Deshabilitado</Button>);
    const button = screen.getByRole('button', { name: /deshabilitado/i });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('handles loading state with aria-busy and disables interaction', async () => {
    const handleClick = vi.fn();
    render(<Button loading onClick={handleClick}>Guardar</Button>);
    const button = screen.getByRole('button', { name: /guardar/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    await userEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
    // Check loading indicator icon/spinner
    expect(screen.getByTestId('button-spinner')).toBeInTheDocument();
  });

  it('renders with destructive variant styles', () => {
    render(<Button variant="destructive">Anular Turno</Button>);
    const button = screen.getByRole('button', { name: /anular turno/i });
    expect(button.className).toContain('bg-destructive');
  });
});
