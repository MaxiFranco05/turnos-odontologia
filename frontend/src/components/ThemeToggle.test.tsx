import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle (Strict TDD - Modern UI Component)', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('renders modern toggle switch with role="switch" and aria-checked="false" in light mode', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDefined();
    expect(toggle.getAttribute('aria-checked')).toBe('false');
    expect(toggle.getAttribute('aria-label')).toBe('Cambiar a modo oscuro');
    expect(toggle.getAttribute('title')).toBe('Cambiar a modo oscuro');
  });

  it('renders toggle switch with aria-checked="true" in dark mode', () => {
    render(
      <ThemeProvider defaultTheme="dark">
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggle = screen.getByRole('switch');
    expect(toggle.getAttribute('aria-checked')).toBe('true');
    expect(toggle.getAttribute('aria-label')).toBe('Cambiar a modo claro');
    expect(toggle.getAttribute('title')).toBe('Cambiar a modo claro');
  });

  it('toggles theme, updates aria-checked and root element class when clicked', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggle = screen.getByRole('switch');
    expect(toggle.getAttribute('aria-checked')).toBe('false');
    expect(document.documentElement.classList.contains('dark')).toBe(false);

    fireEvent.click(toggle);

    expect(toggle.getAttribute('aria-checked')).toBe('true');
    expect(toggle.getAttribute('aria-label')).toBe('Cambiar a modo claro');
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    fireEvent.click(toggle);

    expect(toggle.getAttribute('aria-checked')).toBe('false');
    expect(toggle.getAttribute('aria-label')).toBe('Cambiar a modo oscuro');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('supports custom className prop for flexible positioning', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <ThemeToggle className="custom-test-class" />
      </ThemeProvider>
    );

    const toggle = screen.getByRole('switch');
    expect(toggle.className).toContain('custom-test-class');
  });
});
