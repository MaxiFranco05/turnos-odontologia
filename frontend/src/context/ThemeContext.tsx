import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeContextValue {
  theme: ThemeMode;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

export interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: ThemeMode;
  storageKey?: string;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined' || !window.matchMedia) {
    return 'light';
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'clinic-theme',
}: ThemeProviderProps): React.JSX.Element {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return defaultTheme;
    try {
      const stored = localStorage.getItem(storageKey) as ThemeMode | null;
      if (stored === 'light' || stored === 'dark' || stored === 'system') {
        return stored;
      }
    } catch {
      // LocalStorage access might fail in restricted environments
    }
    return defaultTheme;
  });

  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>(getSystemTheme);

  // Listen to system dark/light preference changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener?.('change', handleChange);
    return () => {
      mediaQuery.removeEventListener?.('change', handleChange);
    };
  }, []);

  const resolvedTheme: 'light' | 'dark' = useMemo(() => {
    return theme === 'system' ? systemTheme : theme;
  }, [theme, systemTheme]);

  // Synchronize document.documentElement class
  useEffect(() => {
    const root = document.documentElement;
    if (resolvedTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [resolvedTheme]);

  const setTheme = useCallback(
    (newTheme: ThemeMode) => {
      try {
        localStorage.setItem(storageKey, newTheme);
      } catch {
        // LocalStorage fallback
      }
      setThemeState(newTheme);
    },
    [storageKey]
  );

  const toggleTheme = useCallback(() => {
    const nextTheme = resolvedTheme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  }, [resolvedTheme, setTheme]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
      toggleTheme,
    }),
    [theme, resolvedTheme, setTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
