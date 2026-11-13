import type { RolUsuario } from '@/types/auth';

export interface DemoAccount {
  role: RolUsuario;
  title: string;
  sub: string;
  identificador: string;
  password: string;
}

export const DEMO_ACCOUNTS: readonly DemoAccount[] = [
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

const OVERRIDE_KEY_PREFIX = 'demo_override_password_';

function getOverrideKey(identificador: string): string {
  return `${OVERRIDE_KEY_PREFIX}${identificador.trim().toLowerCase()}`;
}

function isDemoIdentifier(identificador: string): boolean {
  const normalized = identificador.trim().toLowerCase();
  return DEMO_ACCOUNTS.some((account) => account.identificador.toLowerCase() === normalized);
}

/**
 * Busca la cuenta demo configurada para un rol dado.
 */
export function getDemoAccountByRole(role: RolUsuario): DemoAccount | undefined {
  return DEMO_ACCOUNTS.find((account) => account.role === role);
}

/**
 * Devuelve la contraseña vigente para una cuenta demo (prioriza override en localStorage).
 */
export function getDemoPassword(identificador: string, fallbackPassword?: string): string {
  const normalized = identificador.trim().toLowerCase();
  const defaultPassword =
    fallbackPassword ??
    DEMO_ACCOUNTS.find((account) => account.identificador.toLowerCase() === normalized)?.password ??
    '';

  if (typeof window === 'undefined') {
    return defaultPassword;
  }

  try {
    const override = window.localStorage.getItem(getOverrideKey(normalized));
    return override && override.length > 0 ? override : defaultPassword;
  } catch {
    return defaultPassword;
  }
}

/**
 * Guarda en localStorage la nueva contraseña de una cuenta demo tras un cambio exitoso.
 */
export function saveDemoPasswordOverride(identificador: string, newPassword: string): void {
  if (typeof window === 'undefined' || !isDemoIdentifier(identificador) || !newPassword) {
    return;
  }

  try {
    window.localStorage.setItem(getOverrideKey(identificador), newPassword);
  } catch {
    // Ignore storage quota or private-mode errors
  }
}

/**
 * Elimina el override de contraseña demo almacenado en localStorage (p. ej. ante 401 tras reset de seed).
 */
export function clearDemoPasswordOverride(identificador: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.removeItem(getOverrideKey(identificador));
  } catch {
    // Ignore storage errors
  }
}
