import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SimulatorProvider } from '@/context/SimulatorContext';
import { PhoneSimulatorModal } from './PhoneSimulatorModal';
import { MobileSimulatorButton } from './MobileSimulatorButton';

describe('PhoneSimulatorModal & MobileSimulatorButton', () => {
  it('does not render modal content when simulator is closed', () => {
    render(
      <SimulatorProvider>
        <PhoneSimulatorModal />
      </SimulatorProvider>
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders phone chassis, dynamic island, and iframe when opened via button', () => {
    render(
      <SimulatorProvider>
        <MobileSimulatorButton />
        <PhoneSimulatorModal />
      </SimulatorProvider>
    );

    // Initial state: modal closed
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    // Click trigger button
    const openBtn = screen.getByRole('button', { name: /abrir simulador móvil/i });
    expect(openBtn).toBeInTheDocument();
    fireEvent.click(openBtn);

    // Modal dialog is now visible
    const dialog = screen.getByRole('dialog', { name: /simulador de dispositivo móvil/i });
    expect(dialog).toBeInTheDocument();

    // Check header elements
    expect(screen.getByText('iPhone 15 Pro')).toBeInTheDocument();
    expect(screen.getByText('390 × 844')).toBeInTheDocument();

    // Check iframe viewport
    const iframe = screen.getByTitle('Vista Móvil Simulada');
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('src')).toContain('simulated_mobile=true');

    // Click reload button
    const reloadBtn = screen.getByRole('button', { name: /recargar vista móvil/i });
    fireEvent.click(reloadBtn);
    expect(screen.getByTitle('Vista Móvil Simulada')).toBeInTheDocument();

    // Click close button
    const closeBtn = screen.getByRole('button', { name: /cerrar simulador móvil/i });
    fireEvent.click(closeBtn);

    // Modal is dismissed
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes modal when clicking backdrop area', () => {
    render(
      <SimulatorProvider>
        <MobileSimulatorButton />
        <PhoneSimulatorModal />
      </SimulatorProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /abrir simulador móvil/i }));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();

    // Clicking the backdrop itself
    fireEvent.click(dialog);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
