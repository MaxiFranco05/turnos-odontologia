import React, { useState, useRef, useMemo } from 'react';
import { X, RotateCcw, Smartphone, ExternalLink } from 'lucide-react';
import { useSimulator } from '@/context/SimulatorContext';

export interface PhoneSimulatorModalProps {
  initialPath?: string;
}

export const PhoneSimulatorModal: React.FC<PhoneSimulatorModalProps> = ({ initialPath }) => {
  const { isOpen, closeSimulator, isInsideIframe } = useSimulator();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const iframeSrc = useMemo(() => {
    if (typeof window === 'undefined') return '';
    const origin = window.location.origin;
    const path = initialPath || window.location.pathname;
    const search = window.location.search;
    const delimiter = search ? '&' : '?';
    return `${origin}${path}${search}${delimiter}simulated_mobile=true`;
  }, [initialPath, reloadKey]);

  const handleReload = () => {
    setReloadKey((prev) => prev + 1);
  };

  const handleOpenNewTab = () => {
    if (typeof window !== 'undefined') {
      window.open(iframeSrc, '_blank', 'noopener,noreferrer');
    }
  };

  // Do not render simulator recursively if already within an iframe, or when closed
  if (isInsideIframe || !isOpen) {
    return null;
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Simulador de dispositivo móvil"
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          closeSimulator();
        }
      }}
    >
      {/* Top Controller Bar */}
      <header className="w-full max-w-[420px] mb-2 sm:mb-3 flex items-center justify-between px-2 text-white/90">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Smartphone className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="text-xs font-semibold tracking-tight text-white">iPhone 15 Pro</span>
              <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/20 px-1.5 py-0.2 rounded-full border border-cyan-500/30">
                390 × 844
              </span>
            </div>
            <span className="text-[10px] text-zinc-400 block -mt-0.5">Vista móvil interactiva</span>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={handleReload}
            className="p-1.5 rounded-lg text-zinc-300 hover:text-white hover:bg-white/10 active:scale-95 transition-all"
            title="Recargar vista móvil"
            aria-label="Recargar vista móvil"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleOpenNewTab}
            className="p-1.5 rounded-lg text-zinc-300 hover:text-white hover:bg-white/10 active:scale-95 transition-all"
            title="Abrir en pestaña independiente"
            aria-label="Abrir en pestaña independiente"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={closeSimulator}
            className="p-1.5 rounded-lg text-zinc-300 hover:text-white hover:bg-red-500/20 hover:text-red-300 active:scale-95 transition-all ml-1 border border-white/10"
            title="Cerrar simulador (Esc)"
            aria-label="Cerrar simulador móvil"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* iPhone Physical Chassis */}
      <div className="relative w-[390px] h-[780px] max-h-[85vh] rounded-[48px] border-[10px] border-slate-800 dark:border-zinc-800 bg-slate-50 dark:bg-[#09090b] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.7)] flex flex-col overflow-hidden ring-1 ring-white/15 shrink-0 transition-transform select-none">
        {/* Embedded Iframe Viewport (100% clean, unobstructed header) */}
        <div className="relative flex-1 w-full h-full overflow-hidden bg-background">
          <iframe
            key={reloadKey}
            ref={iframeRef}
            src={iframeSrc}
            title="Vista Móvil Simulada"
            className="w-full h-full border-0 select-auto"
            allow="clipboard-read; clipboard-write"
          />
        </div>

        {/* iPhone Home Indicator Bar */}
        <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 z-30 w-32 h-1 rounded-full bg-slate-400/60 dark:bg-zinc-600/60 pointer-events-none" />
      </div>

      {/* Esc shortcut badge */}
      <footer className="mt-2 text-[11px] text-zinc-400 flex items-center space-x-1.5">
        <span>Presioná</span>
        <kbd className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-white/10 border border-white/20 rounded text-zinc-200">
          ESC
        </kbd>
        <span>o hacé clic afuera para volver al escritorio</span>
      </footer>
    </div>
  );
};

export default PhoneSimulatorModal;
