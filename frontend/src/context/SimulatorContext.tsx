import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';

export interface SimulatorContextType {
  isOpen: boolean;
  openSimulator: () => void;
  closeSimulator: () => void;
  toggleSimulator: () => void;
  isInsideIframe: boolean;
}

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

/**
 * Checks whether the current window is embedded within an iframe or in simulation mode.
 * Evaluates window.self vs window.top and the simulated_mobile URL query parameter.
 */
export const checkIsInsideIframe = (): boolean => {
  if (typeof window === 'undefined') return false;
  try {
    const isEmbedded = window.self !== window.top;
    const hasQueryParam = new URLSearchParams(window.location.search).get('simulated_mobile') === 'true';
    return isEmbedded || hasQueryParam;
  } catch {
    return true;
  }
};

export const SimulatorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isInsideIframe = useMemo(() => checkIsInsideIframe(), []);

  const openSimulator = useCallback(() => {
    if (!isInsideIframe) {
      setIsOpen(true);
    }
  }, [isInsideIframe]);

  const closeSimulator = useCallback(() => {
    setIsOpen(false);
  }, []);

  const toggleSimulator = useCallback(() => {
    if (!isInsideIframe) {
      setIsOpen((prev) => !prev);
    }
  }, [isInsideIframe]);

  // Lock background scroll when simulator modal is open
  useEffect(() => {
    if (typeof document === 'undefined') return;
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  // Global Escape key listener to dismiss the phone frame
  useEffect(() => {
    if (!isOpen || typeof window === 'undefined') return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeSimulator();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeSimulator]);

  const contextValue = useMemo<SimulatorContextType>(
    () => ({
      isOpen,
      openSimulator,
      closeSimulator,
      toggleSimulator,
      isInsideIframe,
    }),
    [isOpen, openSimulator, closeSimulator, toggleSimulator, isInsideIframe]
  );

  return (
    <SimulatorContext.Provider value={contextValue}>
      {children}
    </SimulatorContext.Provider>
  );
};

export const useSimulator = (): SimulatorContextType => {
  const context = useContext(SimulatorContext);
  if (!context) {
    throw new Error('useSimulator must be used within a SimulatorProvider');
  }
  return context;
};

export const useOptionalSimulator = (): SimulatorContextType | null => {
  return useContext(SimulatorContext) ?? null;
};
