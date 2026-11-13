import React from 'react';
import { Smartphone } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useOptionalSimulator } from '@/context/SimulatorContext';

export interface MobileSimulatorButtonProps {
  className?: string;
  variant?: 'outline' | 'default' | 'ghost' | 'secondary';
  showLabel?: boolean;
}

export const MobileSimulatorButton: React.FC<MobileSimulatorButtonProps> = ({
  className,
  variant = 'outline',
  showLabel = true,
}) => {
  const simulator = useOptionalSimulator();

  // Hide the trigger when already running inside a simulated frame
  if (!simulator || simulator.isInsideIframe) {
    return null;
  }

  return (
    <Button
      variant={variant}
      size="sm"
      onClick={simulator.openSimulator}
      className={`rounded-full h-8 px-2.5 text-xs flex items-center space-x-1.5 text-slate-700 dark:text-zinc-200 hover:text-cyan-600 dark:hover:text-cyan-400 border-slate-200/80 dark:border-zinc-700/80 active:scale-95 transition-all shadow-sm ${className ?? ''}`}
      aria-label="Abrir simulador móvil"
      title="Ver vista móvil interactiva (390px)"
    >
      <Smartphone className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400 shrink-0" />
      {showLabel && <span className="hidden xl:inline font-medium whitespace-nowrap">Vista Móvil</span>}
    </Button>
  );
};

export default MobileSimulatorButton;
