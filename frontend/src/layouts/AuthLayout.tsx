import React from 'react';
import { Outlet } from 'react-router-dom';
import { Stethoscope } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-slate-50 p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center space-y-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Stethoscope className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Turnos Odontología
          </h1>
          <p className="text-sm text-slate-500">
            Sistema Integral de Gestión de Agenda Odontológica
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
