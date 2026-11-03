export type RolUsuario = 'paciente' | 'recepcion' | 'odontologo';

export interface UserProfile {
  id: number;
  email: string;
  identificador?: string;
  rol: RolUsuario;
  nombre: string;
  apellido: string;
  debe_cambiar_password?: boolean;
  perfil_completo?: boolean;
}

export interface LoginRequestPayload {
  identificador: string;
  password: string;
}

export interface ChangePasswordRequestPayload {
  password_actual: string;
  password_nueva: string;
  nombre?: string | null;
  email?: string | null;
}

export interface TokenResponsePayload {
  access_token: string;
  token_type: string;
  rol: RolUsuario;
  debe_cambiar_password: boolean;
  perfil_completo: boolean;
}

export interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
}

export function getDefaultRouteForUser(
  user: (Pick<UserProfile, 'rol'> & Partial<Pick<UserProfile, 'debe_cambiar_password'>>) | null
): string {
  if (!user) return '/login';
  if (user.debe_cambiar_password === true) return '/cambiar-password';
  switch (user.rol) {
    case 'recepcion':
      return '/recepcion/agenda';
    case 'odontologo':
      return '/odontologo/agenda';
    case 'paciente':
      return '/paciente/mis-turnos';
    default:
      return '/login';
  }
}
