import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { useOptionalAuth } from '@/context/AuthContext';
import { useChangePasswordMutation } from '@/hooks/useAuthMutations';
import { getDefaultRouteForUser } from '@/types/auth';

export const CambiarPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const auth = useOptionalAuth();
  const changeMutation = useChangePasswordMutation();

  const user = auth?.user;

  const [passwordActual, setPasswordActual] = useState('');
  const [passwordNueva, setPasswordNueva] = useState('');
  const [confirmarPassword, setConfirmarPassword] = useState('');
  const [nombre, setNombre] = useState(
    user?.nombre && user.nombre !== 'Paciente' && user.nombre !== 'Usuario' ? user.nombre : ''
  );
  const [email, setEmail] = useState(
    user?.email && !user.email.includes('@clinica.com') ? user.email : ''
  );
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string | undefined>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If anonymous, send to /login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If already changed, send to role home
  if (user.debe_cambiar_password === false) {
    return <Navigate to={getDefaultRouteForUser(user)} replace />;
  }

  const isProfileIncomplete = user.perfil_completo === false;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage(null);

    const errors: Record<string, string> = {};

    if (!passwordActual) {
      errors.passwordActual = 'La contraseña actual es requerida';
    }

    if (!passwordNueva) {
      errors.passwordNueva = 'La nueva contraseña es requerida';
    } else if (passwordNueva.length < 8) {
      errors.passwordNueva = 'La contraseña debe tener al menos 8 caracteres';
    } else if (!/[A-Z]/.test(passwordNueva)) {
      errors.passwordNueva = 'La contraseña debe contener al menos una letra mayúscula';
    } else if (!/\d/.test(passwordNueva)) {
      errors.passwordNueva = 'La contraseña debe contener al menos un número';
    } else if (passwordNueva === passwordActual) {
      errors.passwordNueva = 'La nueva contraseña debe ser distinta a la actual';
    }

    if (passwordNueva && confirmarPassword !== passwordNueva) {
      errors.confirmarPassword = 'Las contraseñas no coinciden';
    }

    if (isProfileIncomplete) {
      if (!nombre.trim()) {
        errors.nombre = 'El nombre es requerido para completar su perfil';
      }
      if (!email.trim()) {
        errors.email = 'El correo electrónico es requerido';
      }
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setValidationErrors({});

    changeMutation.mutate(
      {
        password_actual: passwordActual,
        password_nueva: passwordNueva,
        nombre: isProfileIncomplete && nombre.trim() ? nombre.trim() : undefined,
        email: isProfileIncomplete && email.trim() ? email.trim() : undefined,
      },
      {
        onSuccess: (data) => {
          const nextRoute = getDefaultRouteForUser(data);
          navigate(nextRoute, { replace: true });
        },
        onError: (err: any) => {
          const detail = err?.response?.data?.detail;
          if (typeof detail === 'string') {
            setErrorMessage(detail);
          } else {
            setErrorMessage('Error al actualizar la contraseña. Verifique los datos ingresados.');
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1">
        <div className="flex items-center space-x-2 text-primary">
          <ShieldCheck className="h-5 w-5" />
          <span className="text-xs font-semibold uppercase tracking-wider">Seguridad de la Cuenta</span>
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-slate-900">
          Cambio Obligatorio de Contraseña
        </h2>
        <p className="text-sm text-slate-500">
          Por seguridad, debe actualizar su contraseña temporal antes de continuar al sistema.
        </p>
      </div>

      {errorMessage && (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <Input
            id="passwordActual"
            label="Contraseña actual"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={passwordActual}
            onChange={(e) => {
              setPasswordActual(e.target.value);
              if (validationErrors.passwordActual) {
                setValidationErrors((prev) => ({ ...prev, passwordActual: undefined }));
              }
            }}
            error={validationErrors.passwordActual}
            disabled={changeMutation.isPending}
            autoComplete="current-password"
            autoFocus
          />
        </div>

        <div className="relative">
          <Input
            id="passwordNueva"
            label="Nueva contraseña"
            type={showPassword ? 'text' : 'password'}
            placeholder="Mínimo 8 caracteres, 1 mayúscula y 1 número"
            value={passwordNueva}
            onChange={(e) => {
              setPasswordNueva(e.target.value);
              if (validationErrors.passwordNueva) {
                setValidationErrors((prev) => ({ ...prev, passwordNueva: undefined }));
              }
            }}
            error={validationErrors.passwordNueva}
            disabled={changeMutation.isPending}
            autoComplete="new-password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600 focus:outline-none"
            aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>

        <div>
          <Input
            id="confirmarPassword"
            label="Confirmar nueva contraseña"
            type={showPassword ? 'text' : 'password'}
            placeholder="Repita la nueva contraseña"
            value={confirmarPassword}
            onChange={(e) => {
              setConfirmarPassword(e.target.value);
              if (validationErrors.confirmarPassword) {
                setValidationErrors((prev) => ({ ...prev, confirmarPassword: undefined }));
              }
            }}
            error={validationErrors.confirmarPassword}
            disabled={changeMutation.isPending}
            autoComplete="new-password"
          />
        </div>

        {isProfileIncomplete && (
          <div className="rounded-lg border border-border bg-muted/40 p-4 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Completar Perfil de Paciente
            </h3>
            <Input
              id="nombre"
              label="Nombre y Apellido"
              type="text"
              placeholder="ej. Lucía Fernández"
              value={nombre}
              onChange={(e) => {
                setNombre(e.target.value);
                if (validationErrors.nombre) {
                  setValidationErrors((prev) => ({ ...prev, nombre: undefined }));
                }
              }}
              error={validationErrors.nombre}
              disabled={changeMutation.isPending}
            />
            <Input
              id="email"
              label="Correo electrónico"
              type="email"
              placeholder="ej. lucia@gmail.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (validationErrors.email) {
                  setValidationErrors((prev) => ({ ...prev, email: undefined }));
                }
              }}
              error={validationErrors.email}
              disabled={changeMutation.isPending}
            />
          </div>
        )}

        <Button
          type="submit"
          loading={changeMutation.isPending}
          disabled={changeMutation.isPending}
          className="w-full active:scale-[0.98] transition-transform duration-150 ease-out"
        >
          Actualizar Contraseña
        </Button>
      </form>
    </div>
  );
};

export default CambiarPasswordPage;
