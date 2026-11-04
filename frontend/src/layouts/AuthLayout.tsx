import React from 'react';
import { Outlet } from 'react-router-dom';
import { Stethoscope } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

export const AuthLayout: React.FC = () => {
  return (
    <div className="relative flex min-h-[100dvh] flex-col items-center justify-center bg-slate-50 dark:bg-background p-4 sm:p-6 lg:p-8 transition-colors duration-200">
      {/* Top right theme toggle */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center space-y-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Stethoscope className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-foreground">
            Turnos Odontología
          </h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground">
            Sistema Integral de Gestión de Agenda Odontológica
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-border bg-white dark:bg-card p-6 shadow-sm sm:p-8 transition-colors duration-200">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
