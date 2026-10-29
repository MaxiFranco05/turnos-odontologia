import React from 'react';
import { useAuth } from '@/context/AuthContext';
import { router } from '@/router/routes';
import type { RolUsuario } from '@/types/auth';

export const DevToolbar: React.FC = () => {
  const { user, loginAs, logout } = useAuth();

  const handleSelectRole = (role: RolUsuario | 'public'): void => {
    if (role === 'public') {
      logout();
      router.navigate('/login');
    } else {
      loginAs(role);
      if (role === 'recepcion') {
        router.navigate('/recepcion/agenda');
      } else if (role === 'odontologo') {
        router.navigate('/odontologo/agenda');
      } else if (role === 'paciente') {
        router.navigate('/paciente/disponibilidad');
      }
    }
  };

  return (
    <aside
      aria-label="Simulador de roles para desarrollo"
      className="fixed bottom-4 right-4 z-50 flex items-center space-x-2 rounded-xl border border-slate-300 bg-white/95 p-2 text-xs shadow-xl backdrop-blur-sm"
    >
      <span className="font-semibold text-slate-500">Simulador C-11:</span>
      <button
        type="button"
        onClick={() => handleSelectRole('public')}
        className={`rounded px-2.5 py-1.5 font-medium transition-colors ${
          user === null
            ? 'bg-slate-900 text-white shadow-sm'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        Público (Login)
      </button>
      <button
        type="button"
        onClick={() => handleSelectRole('recepcion')}
        className={`rounded px-2.5 py-1.5 font-medium transition-colors ${
          user?.rol === 'recepcion'
            ? 'bg-primary text-white shadow-sm'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        Recepción
      </button>
      <button
        type="button"
        onClick={() => handleSelectRole('odontologo')}
        className={`rounded px-2.5 py-1.5 font-medium transition-colors ${
          user?.rol === 'odontologo'
            ? 'bg-primary text-white shadow-sm'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        Odontólogo
      </button>
      <button
        type="button"
        onClick={() => handleSelectRole('paciente')}
        className={`rounded px-2.5 py-1.5 font-medium transition-colors ${
          user?.rol === 'paciente'
            ? 'bg-primary text-white shadow-sm'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        Paciente
      </button>
    </aside>
  );
};

export default DevToolbar;
