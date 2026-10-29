import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import type { UserProfile, RolUsuario } from '@/types/auth';
import { useOptionalAuth } from '@/context/AuthContext';

export interface ProtectedRouteProps {
  user?: UserProfile | null;
  allowedRoles?: RolUsuario[];
  redirectPath?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  user: propUser,
  allowedRoles,
  redirectPath = '/login',
}) => {
  const auth = useOptionalAuth();
  const location = useLocation();
  const activeUser = propUser !== undefined ? propUser : auth?.user ?? null;

  if (!activeUser) {
    return <Navigate to={redirectPath} replace />;
  }

  if (activeUser.debe_cambiar_password === true && location.pathname !== '/cambiar-password') {
    return <Navigate to="/cambiar-password" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(activeUser.rol)) {
    // If user's role is not allowed, redirect to their home
    const roleDefaultRoutes: Record<RolUsuario, string> = {
      recepcion: '/recepcion/agenda',
      odontologo: '/odontologo/agenda',
      paciente: '/paciente/mis-turnos',
    };
    return <Navigate to={roleDefaultRoutes[activeUser.rol] || '/login'} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
