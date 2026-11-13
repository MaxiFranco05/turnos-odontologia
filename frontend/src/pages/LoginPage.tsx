import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { useOptionalAuth } from '@/context/AuthContext';
import { useLoginMutation } from '@/hooks/useAuthMutations';
import { getDefaultRouteForUser } from '@/types/auth';

const DEMO_ACCOUNTS = [
  {
    role: 'recepcion',
    title: 'Demo Recepción',
    sub: 'Recepción Central',
    identificador: 'recepcion@turnosodontologia.com',
    password: 'Admin1234!',
  },
  {
    role: 'odontologo',
    title: 'Demo Odontólogo',
    sub: 'Dra. Sofía Martín',
    identificador: 'sofia.martin@turnosodontologia.com',
    password: 'Dentist1234!',
  },
  {
    role: 'paciente',
    title: 'Demo Paciente',
    sub: 'Lucía Gómez',
    identificador: 'lucia.gomez@example.com',
    password: 'Patient1234!',
  },
];

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const auth = useOptionalAuth();
  const loginMutation = useLoginMutation();

  const [identificador, setIdentificador] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{
    identificador?: string;
    password?: string;
  }>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If user already authenticated with valid state, redirect immediately
  if (auth?.user) {
    return <Navigate to={getDefaultRouteForUser(auth.user)} replace />;
  }

  const handleFillDemo = (demo: typeof DEMO_ACCOUNTS[number]) => {
    setIdentificador(demo.identificador);
    setPassword(demo.password);
    setValidationErrors({});
    setErrorMessage(null);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage(null);

    const errors: { identificador?: string; password?: string } = {};
    if (!identificador.trim()) {
      errors.identificador = 'El identificador es requerido';
    }
    if (!password) {
      errors.password = 'La contraseña es requerida';
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setValidationErrors({});

    loginMutation.mutate(
      {
        payload: {
          identificador: identificador.trim(),
          password,
        },
        remember,
      },
      {
        onSuccess: (data) => {
          const nextRoute = getDefaultRouteForUser(data);
          navigate(nextRoute, { replace: true });
        },
        onError: (err: any) => {
          const status = err?.response?.status;
          const detail = err?.response?.data?.detail;

          if (status === 401 || detail === 'Credenciales inválidas') {
            setErrorMessage('Credenciales inválidas');
          } else if (status === 429) {
            setErrorMessage('Demasiados intentos fallidos. Intente nuevamente en 60 segundos.');
          } else if (typeof detail === 'string') {
            setErrorMessage(detail);
          } else {
            setErrorMessage('Error al comunicarse con el servidor. Intente nuevamente.');
          }
        },
      }
    );
  };

  return (
    <div className="space-y-4 sm:space-y-6 text-left">
      <div className="space-y-0.5 sm:space-y-1">
        <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-zinc-50">Iniciar Sesión</h2>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-zinc-400">
          Ingrese sus credenciales para acceder a la gestión de turnos odontológicos.
        </p>
      </div>

      {errorMessage && (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-3.5 sm:space-y-4" noValidate>
        <div>
          <Input
            id="identificador"
            label="Correo o N.º de socio"
            type="text"
            placeholder="ej. socio123 o usuario@clinica.com"
            value={identificador}
            onChange={(e) => {
              setIdentificador(e.target.value);
              if (validationErrors.identificador) {
                setValidationErrors((prev) => ({ ...prev, identificador: undefined }));
              }
            }}
            error={validationErrors.identificador}
            disabled={loginMutation.isPending}
            autoComplete="username"
            autoFocus
          />
        </div>

        <div className="relative">
          <Input
            id="password"
            label="Contraseña"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (validationErrors.password) {
                setValidationErrors((prev) => ({ ...prev, password: undefined }));
              }
            }}
            error={validationErrors.password}
            disabled={loginMutation.isPending}
            autoComplete="current-password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600 dark:hover:text-zinc-200 focus:outline-none"
            aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>

        <div className="flex items-center justify-between pt-0.5 sm:pt-1">
          <label className="flex items-center space-x-2 text-xs sm:text-sm text-slate-600 dark:text-zinc-400 cursor-pointer select-none">
            <input
              type="checkbox"
              id="remember"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              disabled={loginMutation.isPending}
              className="h-4 w-4 rounded border-slate-300 dark:border-zinc-700 text-primary focus:ring-primary"
            />
            <span>Recordar en este equipo</span>
          </label>
        </div>

        <Button
          type="submit"
          loading={loginMutation.isPending}
          disabled={loginMutation.isPending}
          className="w-full active:scale-[0.96] transition-transform duration-150 ease-out flex items-center justify-center gap-2 rounded-xl py-2.5 font-semibold"
        >
          <span>Iniciar Sesión</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>

      {/* Quick 1-Click Access Pill Selector */}
      <div className="mt-4 sm:mt-6 pt-3.5 sm:pt-5 border-t border-slate-200/60 dark:border-zinc-800/80">
        <span className="text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-zinc-500 block mb-2 text-center">
          Acceso Rápido de Demostración
        </span>
        <div className="grid grid-cols-3 gap-1.5 sm:gap-2">
          {DEMO_ACCOUNTS.map((demo) => (
            <button
              key={demo.role}
              type="button"
              onClick={() => handleFillDemo(demo)}
              className="p-1.5 sm:p-2 rounded-xl bg-slate-100/80 dark:bg-zinc-800/80 hover:bg-cyan-50 dark:hover:bg-cyan-950/40 border border-transparent hover:border-cyan-200 dark:hover:border-cyan-800 text-slate-700 dark:text-zinc-300 active:scale-[0.96] transition-all text-center flex flex-col items-center justify-center"
              aria-label={demo.title}
            >
              <span className="font-semibold text-[10px] sm:text-[11px] block">{demo.title.replace('Demo ', '')}</span>
              <span className="text-[9px] sm:text-[10px] text-slate-400 dark:text-zinc-500 block">{demo.sub}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
