import React from 'react';
import { useTheme } from '../context/ThemeContext';

export interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className = '' }: ThemeToggleProps): React.JSX.Element {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const label = isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={label}
      title={label}
      onClick={toggleTheme}
      className={`group relative inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border border-slate-300 dark:border-neutral-700 bg-slate-200 dark:bg-neutral-800 p-0.5 shadow-inner transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 active:scale-95 ${className}`}
    >
      {/* Sliding Thumb containing the active mode icon */}
      <span
        className={`pointer-events-none inline-flex h-6 w-6 items-center justify-center rounded-full bg-white dark:bg-neutral-900 shadow-md ring-0 transition-transform duration-200 ease-out transform ${
          isDark ? 'translate-x-5 border border-neutral-700' : 'translate-x-0 border border-slate-200/80'
        }`}
      >
        {isDark ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5 text-cyan-400 drop-shadow-sm transition-transform duration-200"
            aria-hidden="true"
          >
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5 text-amber-500 drop-shadow-sm transition-transform duration-200"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2" />
            <path d="M12 20v2" />
            <path d="m4.93 4.93 1.41 1.41" />
            <path d="m17.66 17.66 1.41 1.41" />
            <path d="M2 12h2" />
            <path d="M20 12h2" />
            <path d="m6.34 17.66-1.41 1.41" />
            <path d="m19.07 4.93-1.41 1.41" />
          </svg>
        )}
      </span>
    </button>
  );
}

export default ThemeToggle;
