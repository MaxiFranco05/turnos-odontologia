import React from 'react';
import { Outlet } from 'react-router-dom';
import { Stethoscope } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { MobileSimulatorButton } from '@/components/MobileSimulatorButton';

export const AuthLayout: React.FC = () => {
  return (
    <div className="relative flex min-h-[100dvh] w-full flex-col items-center justify-start sm:justify-center bg-slate-50 dark:bg-[#09090b] p-4 py-6 sm:p-6 lg:p-8 transition-colors duration-200 overflow-x-hidden overflow-y-auto">
      {/* Ambient Dental Radial Glow (clipped to viewport container so it never triggers scrollbars) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-80 h-80 bg-cyan-500/15 dark:bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-sky-500/15 dark:bg-sky-500/10 rounded-full blur-3xl" />
      </div>

      {/* Top right controls: Simulator & Theme Toggle */}
      <div className="absolute top-3 right-3 sm:top-6 sm:right-6 z-10 flex items-center space-x-2">
        <MobileSimulatorButton />
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-4 sm:space-y-6 relative z-10 my-auto">
        {/* Branding & Medical Emblem */}
        <div className="flex flex-col items-center space-y-1.5 sm:space-y-2 text-center pt-2 sm:pt-0">
          <div className="flex h-11 w-11 sm:h-12 sm:w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-600 via-sky-500 to-teal-400 text-white shadow-lg shadow-cyan-500/25">
            <Stethoscope className="h-5 w-5 sm:h-6 sm:w-6" />
          </div>
          <span className="text-[10px] sm:text-xs font-semibold tracking-wider text-cyan-600 dark:text-cyan-400 uppercase">
            Clínica Odontológica Especializada
          </span>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-foreground">
            Turnos Odontología
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-muted-foreground">
            Sistema Integral de Gestión de Agenda Odontológica
          </p>
        </div>

        {/* Frosted Glass Login Card */}
        <div className="glass-surface rounded-3xl border border-white/60 dark:border-white/10 p-5 sm:p-8 shadow-2xl transition-colors duration-200">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
