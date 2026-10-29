export type RolUsuario = 'paciente' | 'recepcion' | 'odontologo';

export interface UserProfile {
  id: number;
  email: string;
  rol: RolUsuario;
  nombre: string;
  apellido: string;
}

export interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
}
