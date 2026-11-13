import React, { useState } from 'react';
import { Sliders, X, Check } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/context/AuthContext';
import { useOptionalSimulator } from '@/context/SimulatorContext';
import { useLoginMutation } from '@/hooks/useAuthMutations';
import {
  clearDemoPasswordOverride,
  getDemoAccountByRole,
  getDemoPassword,
} from '@/lib/demoCredentials';
import { router } from '@/router/routes';
import { getDefaultRouteForUser, type RolUsuario } from '@/types/auth';

function getErrorStatus(err: unknown): number | undefined {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: unknown }).response;
    if (typeof response === 'object' && response !== null && 'status' in response) {
      const status = (response as { status?: unknown }).status;
      return typeof status === 'number' ? status : undefined;
    }
  }
  return undefined;
}

export const DevToolbar: React.FC = () => {
  const { user, logout } = useAuth();
  const simulator = useOptionalSimulator();
  const queryClient = useQueryClient();
  const loginMutation = useLoginMutation();
  const [isOpen, setIsOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If inside simulated phone iframe, hide dev toolbar
  if (simulator?.isInsideIframe) {
    return null;
  }

  const handleSelectRole = (role: RolUsuario | 'public'): void => {
    if (loginMutation.isPending) {
      return;
    }

    setErrorMessage(null);

    if (role === 'public') {
      logout();
      queryClient.clear();
      setIsOpen(false);
      router.navigate('/login');
      return;
    }

    const account = getDemoAccountByRole(role);
    if (!account) {
      return;
    }

    const password = getDemoPassword(account.identificador, account.password);

    loginMutation.mutate(
      {
        payload: {
          identificador: account.identificador,
          password,
        },
        remember: true,
      },
      {
        onSuccess: (data) => {
          queryClient.clear();
          setIsOpen(false);
          router.navigate(getDefaultRouteForUser(data));
        },
        onError: (err: unknown) => {
          const status = getErrorStatus(err);
          if (status === 401) {
            clearDemoPasswordOverride(account.identificador);
            setErrorMessage('Credenciales demo inválidas. Reintente con la contraseña por defecto.');
          } else {
            setErrorMessage('No se pudo iniciar sesión con la cuenta demo.');
          }
        },
      }
    );
  };

  return (
    <aside
      aria-label="Selector rápido de rol"
      className="fixed bottom-20 md:bottom-5 right-3 md:right-4 z-50 flex flex-col items-end"
    >
      {/* Expanded Popover Card */}
      {isOpen && (
        <div
          className="mb-2 w-64 rounded-2xl border border-slate-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur-md animate-in fade-in zoom-in-95 duration-150"
        >
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 dark:border-zinc-800">
            <div className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-800 dark:text-zinc-200">Cambio rápido de rol:</span>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
              aria-label="Cerrar simulador"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {errorMessage && (
            <p
              role="alert"
              className="mb-2 rounded-lg bg-red-50 dark:bg-red-950/40 px-2.5 py-1.5 text-[11px] text-red-700 dark:text-red-300"
            >
              {errorMessage}
            </p>
          )}

          <div className="flex flex-col space-y-1.5">
            <button
              type="button"
              disabled={loginMutation.isPending}
              onClick={() => handleSelectRole('public')}
              className={`flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                user === null
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-slate-100 dark:bg-zinc-800/80 text-slate-700 dark:text-zinc-200 hover:bg-slate-200 dark:hover:bg-zinc-700'
              }`}
            >
              <span>Público (Login)</span>
              {user === null && <Check className="w-3.5 h-3.5" />}
            </button>
            <button
              type="button"
              disabled={loginMutation.isPending}
              onClick={() => handleSelectRole('recepcion')}
              className={`flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                user?.rol === 'recepcion'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-slate-100 dark:bg-zinc-800/80 text-slate-700 dark:text-zinc-200 hover:bg-slate-200 dark:hover:bg-zinc-700'
              }`}
            >
              <span>Recepción</span>
              {user?.rol === 'recepcion' && <Check className="w-3.5 h-3.5" />}
            </button>
            <button
              type="button"
              disabled={loginMutation.isPending}
              onClick={() => handleSelectRole('odontologo')}
              className={`flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                user?.rol === 'odontologo'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-slate-100 dark:bg-zinc-800/80 text-slate-700 dark:text-zinc-200 hover:bg-slate-200 dark:hover:bg-zinc-700'
              }`}
            >
              <span>Odontólogo</span>
              {user?.rol === 'odontologo' && <Check className="w-3.5 h-3.5" />}
            </button>
            <button
              type="button"
              disabled={loginMutation.isPending}
              onClick={() => handleSelectRole('paciente')}
              className={`flex items-center justify-between rounded-xl px-2.5 py-1.5 text-xs font-medium transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                user?.rol === 'paciente'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-slate-100 dark:bg-zinc-800/80 text-slate-700 dark:text-zinc-200 hover:bg-slate-200 dark:hover:bg-zinc-700'
              }`}
            >
              <span>Paciente</span>
              {user?.rol === 'paciente' && <Check className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}

      {/* Floating Collapsible Dot / FAB Trigger */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Abrir simulador de roles"
        title="Simulador de roles (Desarrollo)"
        className="group relative flex h-9 w-9 items-center justify-center rounded-full border border-cyan-500/30 bg-white/95 dark:bg-zinc-900/95 text-cyan-600 dark:text-cyan-400 shadow-xl backdrop-blur-md transition-all duration-150 hover:scale-105 active:scale-95"
      >
        <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-cyan-500" />
        </span>
        <Sliders className="h-4 w-4" />
      </button>
    </aside>
  );
};

export default DevToolbar;
