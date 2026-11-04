import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Calendar, Clock, Stethoscope, LogOut, User as UserIcon } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ThemeToggle } from '@/components/ThemeToggle';
import { cn } from '@/lib/utils';
import { useOptionalAuth } from '@/context/AuthContext';
import type { UserProfile, RolUsuario } from '@/types/auth';

export interface AppLayoutProps {
  user?: UserProfile | null;
  onLogout?: () => void;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: RolUsuario[];
}

const NAV_ITEMS: NavItem[] = [
  // Recepción
  {
    label: 'Agenda del día',
    href: '/recepcion/agenda',
    icon: Calendar,
    roles: ['recepcion'],
  },
  {
    label: 'Plantillas',
    href: '/recepcion/plantillas',
    icon: Clock,
    roles: ['recepcion'],
  },
  // Odontólogo
  {
    label: 'Mi agenda',
    href: '/odontologo/agenda',
    icon: Calendar,
    roles: ['odontologo'],
  },
  // Paciente
  {
    label: 'Buscar turno',
    href: '/paciente/disponibilidad',
    icon: Calendar,
    roles: ['paciente'],
  },
  {
    label: 'Mis turnos',
    href: '/paciente/mis-turnos',
    icon: Clock,
    roles: ['paciente'],
  },
];

const ROLE_LABELS: Record<RolUsuario, string> = {
  recepcion: 'Recepción',
  odontologo: 'Odontólogo',
  paciente: 'Paciente',
};

export const AppLayout: React.FC<AppLayoutProps> = ({ user: propUser, onLogout: propLogout }) => {
  const navigate = useNavigate();
  const auth = useOptionalAuth();

  const user = propUser !== undefined ? propUser : auth?.user ?? null;

  const handleLogout = (): void => {
    if (propLogout) {
      propLogout();
    } else if (auth) {
      auth.logout();
      navigate('/login');
    } else {
      navigate('/login');
    }
  };

  const allowedNavItems = user ? NAV_ITEMS.filter((item) => item.roles.includes(user.rol)) : [];

  return (
    <div className="flex min-h-[100dvh] flex-col bg-slate-50 dark:bg-background transition-colors duration-200">
      {/* Top Header */}
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 dark:border-border bg-white dark:bg-card px-4 sm:px-6 transition-colors duration-200">
        <div className="flex items-center space-x-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Stethoscope className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-foreground">
            Turnos Odontología
          </span>
        </div>

        <div className="flex items-center space-x-3 sm:space-x-4">
          <ThemeToggle />

          {user && (
            <div className="flex items-center space-x-3 sm:space-x-4 border-l border-slate-200 dark:border-border pl-3 sm:pl-4">
              <div className="flex items-center space-x-2 text-sm text-slate-700 dark:text-slate-200">
                <UserIcon className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                <span className="font-medium">
                  {user.nombre} {user.apellido}
                </span>
                <Badge variant="secondary" className="capitalize">
                  {ROLE_LABELS[user.rol]}
                </Badge>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="flex items-center space-x-1.5 text-slate-600 dark:text-slate-300 hover:text-destructive dark:hover:text-destructive"
              >
                <LogOut className="h-4 w-4" />
                <span>Cerrar sesión</span>
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Main Container with Sidebar + Outlet */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-200 dark:border-border bg-white dark:bg-card p-4 transition-colors duration-200">
          <nav className="space-y-1">
            {allowedNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary/10 text-primary font-semibold'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </aside>

        {/* Content View */}
        <main className="flex-1 p-6 lg:p-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
