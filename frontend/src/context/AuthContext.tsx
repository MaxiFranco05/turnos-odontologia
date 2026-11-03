import React, { createContext, useContext, useState } from 'react';
import type { UserProfile, RolUsuario, TokenResponsePayload } from '@/types/auth';
import { clearAuthSession, loadAuthSession, saveAuthSession } from '@/services/authService';
import { setAuthToken } from '@/lib/api';

export const MOCK_USERS: Record<RolUsuario, UserProfile> = {
  recepcion: {
    id: 1,
    email: 'recepcion@clinica.com',
    nombre: 'María',
    apellido: 'López',
    rol: 'recepcion',
    debe_cambiar_password: false,
    perfil_completo: true,
  },
  odontologo: {
    id: 2,
    email: 'carlos.sosa@clinica.com',
    nombre: 'Dr. Carlos',
    apellido: 'Sosa',
    rol: 'odontologo',
    debe_cambiar_password: false,
    perfil_completo: true,
  },
  paciente: {
    id: 3,
    email: 'lucia.fernandez@gmail.com',
    nombre: 'Lucía',
    apellido: 'Fernández',
    rol: 'paciente',
    debe_cambiar_password: false,
    perfil_completo: true,
  },
};

export interface AuthContextType {
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  establishSession: (response: TokenResponsePayload, identifier?: string, remember?: boolean) => void;
  loginAs: (role: RolUsuario) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Synchronous hydration from storage on mount (avoids useEffect per Hard Rule #6)
  const [user, setUser] = useState<UserProfile | null>(() => {
    const session = loadAuthSession();
    return session?.user ?? null;
  });

  const establishSession = (
    response: TokenResponsePayload,
    identifier?: string,
    remember: boolean = true
  ): void => {
    saveAuthSession(response, remember, identifier);
    const session = loadAuthSession();
    if (session) {
      setUser(session.user);
    } else {
      setUser({
        id: 1,
        email: identifier || 'user@clinica.com',
        rol: response.rol,
        nombre: response.rol.charAt(0).toUpperCase() + response.rol.slice(1),
        apellido: 'Usuario',
        debe_cambiar_password: response.debe_cambiar_password,
        perfil_completo: response.perfil_completo,
      });
    }
  };

  const loginAs = (role: RolUsuario): void => {
    const mock = MOCK_USERS[role];
    setAuthToken(`mock-token-${role}`);
    setUser(mock);
  };

  const logout = (): void => {
    clearAuthSession();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, establishSession, loginAs, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useOptionalAuth(): AuthContextType | undefined {
  return useContext(AuthContext);
}

export default AuthContext;
