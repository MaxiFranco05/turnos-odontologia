import apiClient, { getAuthToken, setAuthToken, clearAuthToken } from '@/lib/api';
import type {
  LoginRequestPayload,
  ChangePasswordRequestPayload,
  TokenResponsePayload,
  UserProfile,
  RolUsuario,
} from '@/types/auth';

const USER_META_KEY = 'auth_user_meta';

export interface DecodedJwtPayload {
  sub?: string;
  rol?: RolUsuario;
  debe_cambiar_password?: boolean;
  exp?: number;
}

/**
 * Decodes the base64url payload segment of a JWT string.
 */
export function decodeJwtPayload(token: string): DecodedJwtPayload | null {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length < 2) return null;
  try {
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload) as DecodedJwtPayload;
  } catch {
    return null;
  }
}

/**
 * Submits user credentials to POST /api/auth/login.
 */
export async function loginUser(payload: LoginRequestPayload): Promise<TokenResponsePayload> {
  const response = await apiClient.post<TokenResponsePayload>('/auth/login', {
    identificador: payload.identificador.trim(),
    password: payload.password,
  });
  return response.data;
}

/**
 * Submits mandatory password change to POST /api/auth/cambiar-password.
 * Strictly adheres to backend extra="forbid" by only including non-empty fields.
 */
export async function changePassword(
  payload: ChangePasswordRequestPayload
): Promise<TokenResponsePayload> {
  const requestBody: Record<string, string> = {
    password_actual: payload.password_actual,
    password_nueva: payload.password_nueva,
  };
  if (payload.nombre && payload.nombre.trim()) {
    requestBody.nombre = payload.nombre.trim();
  }
  if (payload.email && payload.email.trim()) {
    requestBody.email = payload.email.trim();
  }

  const response = await apiClient.post<TokenResponsePayload>('/auth/cambiar-password', requestBody);
  return response.data;
}

/**
 * Persists session token and user profile metadata in localStorage (if remember=true) or sessionStorage.
 */
export function saveAuthSession(
  response: TokenResponsePayload,
  remember: boolean = true,
  identifier?: string
): void {
  setAuthToken(response.access_token, remember);

  const claims = decodeJwtPayload(response.access_token);
  const user: UserProfile = {
    id: claims?.sub ? parseInt(claims.sub, 10) || 1 : 1,
    email: identifier && identifier.includes('@') ? identifier : `${claims?.sub ?? 'user'}@clinica.com`,
    rol: response.rol,
    nombre: response.rol.charAt(0).toUpperCase() + response.rol.slice(1),
    apellido: 'Usuario',
    debe_cambiar_password: response.debe_cambiar_password,
    perfil_completo: response.perfil_completo,
  };

  const serialized = JSON.stringify(user);
  try {
    if (remember) {
      sessionStorage.removeItem(USER_META_KEY);
      localStorage.setItem(USER_META_KEY, serialized);
    } else {
      localStorage.removeItem(USER_META_KEY);
      sessionStorage.setItem(USER_META_KEY, serialized);
    }
  } catch {
    // Storage restricted
  }
}

/**
 * Rehydrates the active user session synchronously from storage.
 */
export function loadAuthSession(): { token: string; user: UserProfile } | null {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const raw = localStorage.getItem(USER_META_KEY) || sessionStorage.getItem(USER_META_KEY);
    if (raw) {
      const user = JSON.parse(raw) as UserProfile;
      return { token, user };
    }
  } catch {
    // Parse error, fallback to JWT decode
  }

  const claims = decodeJwtPayload(token);
  if (claims && claims.rol) {
    const user: UserProfile = {
      id: claims.sub ? parseInt(claims.sub, 10) || 1 : 1,
      email: `${claims.sub ?? 'user'}@clinica.com`,
      rol: claims.rol,
      nombre: claims.rol.charAt(0).toUpperCase() + claims.rol.slice(1),
      apellido: 'Usuario',
      debe_cambiar_password: claims.debe_cambiar_password ?? false,
      perfil_completo: true,
    };
    return { token, user };
  }

  return null;
}

/**
 * Clears authentication token and session metadata from all storages.
 */
export function clearAuthSession(): void {
  clearAuthToken();
  try {
    localStorage.removeItem(USER_META_KEY);
    sessionStorage.removeItem(USER_META_KEY);
  } catch {
    // Storage restricted
  }
}
