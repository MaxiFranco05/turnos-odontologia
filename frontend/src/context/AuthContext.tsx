import React, { createContext, useContext, useState } from 'react';
import type { UserProfile, RolUsuario } from '@/types/auth';
import { clearAuthToken, setAuthToken } from '@/lib/api';

export const MOCK_USERS: Record<RolUsuario, UserProfile> = {
  recepcion: {
    id: 1,
    email: 'recepcion@clinica.com',
    nombre: 'María',
    apellido: 'López',
    rol: 'recepcion',
  },
  odontologo: {
    id: 2,
    email: 'carlos.sosa@clinica.com',
    nombre: 'Dr. Carlos',
    apellido: 'Sosa',
    rol: 'odontologo',
  },
  paciente: {
    id: 3,
    email: 'lucia.fernandez@gmail.com',
    nombre: 'Lucía',
    apellido: 'Fernández',
    rol: 'paciente',
  },
};

export interface AuthContextType {
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  loginAs: (role: RolUsuario) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);

  const loginAs = (role: RolUsuario): void => {
    const mock = MOCK_USERS[role];
    setAuthToken(`mock-token-${role}`);
    setUser(mock);
  };

  const logout = (): void => {
    clearAuthToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loginAs, logout }}>
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
