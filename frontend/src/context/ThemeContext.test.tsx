import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import React from 'react';
import { ThemeProvider, useTheme } from './ThemeContext';

function TestConsumer() {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button data-testid="toggle-btn" onClick={toggleTheme}>
        Toggle
      </button>
      <button data-testid="set-dark-btn" onClick={() => setTheme('dark')}>
        Set Dark
      </button>
      <button data-testid="set-light-btn" onClick={() => setTheme('light')}>
        Set Light
      </button>
      <button data-testid="set-system-btn" onClick={() => setTheme('system')}>
        Set System
      </button>
    </div>
  );
}

describe('ThemeContext & useTheme (Strict TDD)', () => {
  const STORAGE_KEY = 'clinic-theme';

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
    vi.restoreAllMocks();

    // Default mock matchMedia to light preference
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('throws an informative error if useTheme is used outside ThemeProvider', () => {
    // Suppress console.error from React during boundary rejection
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow('useTheme must be used within a ThemeProvider');
    consoleSpy.mockRestore();
  });

  it('restores persisted "dark" theme from localStorage on initial render', () => {
    localStorage.setItem(STORAGE_KEY, 'dark');

    render(
      <ThemeProvider storageKey={STORAGE_KEY}>
        <TestConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme').textContent).toBe('dark');
    expect(screen.getByTestId('resolved').textContent).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('toggles from light to dark, updates document class and persists to localStorage', () => {
    render(
      <ThemeProvider defaultTheme="light" storageKey={STORAGE_KEY}>
        <TestConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId('resolved').textContent).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);

    // Toggle to dark
    act(() => {
      screen.getByTestId('toggle-btn').click();
    });

    expect(screen.getByTestId('theme').textContent).toBe('dark');
    expect(screen.getByTestId('resolved').textContent).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    // Toggle back to light
    act(() => {
      screen.getByTestId('toggle-btn').click();
    });

    expect(screen.getByTestId('theme').textContent).toBe('light');
    expect(screen.getByTestId('resolved').textContent).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });

  it('honors system dark preference when theme is set to "system"', () => {
    // Mock system preference matchMedia returning dark
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('prefers-color-scheme: dark'),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    render(
      <ThemeProvider defaultTheme="system" storageKey={STORAGE_KEY}>
        <TestConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme').textContent).toBe('system');
    expect(screen.getByTestId('resolved').textContent).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('allows setting explicit themes via setTheme', () => {
    render(
      <ThemeProvider defaultTheme="light" storageKey={STORAGE_KEY}>
        <TestConsumer />
      </ThemeProvider>
    );

    act(() => {
      screen.getByTestId('set-dark-btn').click();
    });
    expect(screen.getByTestId('theme').textContent).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

    act(() => {
      screen.getByTestId('set-light-btn').click();
    });
    expect(screen.getByTestId('theme').textContent).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
  });
});
