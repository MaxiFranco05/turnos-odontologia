import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  SimulatorProvider,
  useSimulator,
  checkIsInsideIframe,
} from './SimulatorContext';

const TestConsumer: React.FC = () => {
  const { isOpen, openSimulator, closeSimulator, toggleSimulator, isInsideIframe } = useSimulator();

  return (
    <div>
      <span data-testid="is-open">{isOpen ? 'open' : 'closed'}</span>
      <span data-testid="is-inside">{isInsideIframe ? 'inside' : 'top'}</span>
      <button onClick={openSimulator}>Open</button>
      <button onClick={closeSimulator}>Close</button>
      <button onClick={toggleSimulator}>Toggle</button>
    </div>
  );
};

describe('SimulatorContext & checkIsInsideIframe', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('detects when outside iframe by default', () => {
    expect(checkIsInsideIframe()).toBe(false);
  });

  it('provides default closed state and allows open, close, and toggle', () => {
    render(
      <SimulatorProvider>
        <TestConsumer />
      </SimulatorProvider>
    );

    expect(screen.getByTestId('is-open').textContent).toBe('closed');
    expect(screen.getByTestId('is-inside').textContent).toBe('top');

    fireEvent.click(screen.getByText('Open'));
    expect(screen.getByTestId('is-open').textContent).toBe('open');

    fireEvent.click(screen.getByText('Close'));
    expect(screen.getByTestId('is-open').textContent).toBe('closed');

    fireEvent.click(screen.getByText('Toggle'));
    expect(screen.getByTestId('is-open').textContent).toBe('open');

    fireEvent.click(screen.getByText('Toggle'));
    expect(screen.getByTestId('is-open').textContent).toBe('closed');
  });

  it('closes simulator on global Escape key', () => {
    render(
      <SimulatorProvider>
        <TestConsumer />
      </SimulatorProvider>
    );

    fireEvent.click(screen.getByText('Open'));
    expect(screen.getByTestId('is-open').textContent).toBe('open');

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.getByTestId('is-open').textContent).toBe('closed');
  });

  it('throws error when useSimulator is used outside of SimulatorProvider', () => {
    const renderOutside = () => render(<TestConsumer />);
    expect(renderOutside).toThrow('useSimulator must be used within a SimulatorProvider');
  });
});
