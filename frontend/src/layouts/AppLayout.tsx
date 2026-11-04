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
    <div className="relative flex min-h-[100dvh] flex-col bg-slate-50 dark:bg-background transition-colors duration-200">
      
      {/* ========================================================= */}
      {/* DESKTOP VIEW: FLOATING GLASS CAPSULE (hidden on < 768px)  */}
      {/* ========================================================= */}
      <header className="hidden md:flex sticky top-4 z-40 px-4 sm:px-6 w-full justify-center">
        <nav
          aria-label="Navegación principal desktop"
          className="glass-surface w-full max-w-4xl rounded-full px-4 py-2 flex items-center justify-between gap-4 transition-all duration-200 shadow-lg"
        >
          {/* Left: Brand Emblem */}
          <div className="flex items-center space-x-2.5 shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 to-cyan-400 text-white shadow-sm glow-cyan">
              <Stethoscope className="h-4 w-4" />
            </div>
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-foreground">
              Turnos Odontología
            </span>
          </div>

          {/* Center: Segmented Navigation Pills */}
          <div className="flex items-center bg-slate-200/50 dark:bg-zinc-800/60 p-1 rounded-full border border-black/5 dark:border-white/5">
            {allowedNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all duration-150 active:scale-[0.96]',
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/30'
                        : 'text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-100'
                    )
                  }
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>

          {/* Right: User Capsule, Theme Toggle & Logout */}
          <div className="flex items-center space-x-2 shrink-0">
            <ThemeToggle />

            {user && (
              <div className="flex items-center space-x-2 border-l border-slate-200/60 dark:border-zinc-800 pl-2">
                <div className="flex items-center space-x-1.5 text-xs text-slate-700 dark:text-slate-200 bg-slate-100/80 dark:bg-zinc-800/80 px-2.5 py-1 rounded-full border border-slate-200/60 dark:border-zinc-700/60">
                  <UserIcon className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                  <span className="font-medium max-w-[120px] truncate">
                    {user.nombre} {user.apellido}
                  </span>
                  <Badge variant="secondary" className="capitalize text-[10px] px-1.5 py-0">
                    {ROLE_LABELS[user.rol]}
                  </Badge>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLogout}
                  className="rounded-full h-8 px-3 text-xs flex items-center space-x-1 text-slate-600 dark:text-slate-300 hover:text-destructive dark:hover:text-destructive active:scale-[0.96] transition-transform"
                  aria-label="Cerrar sesión"
                  title="Cerrar sesión"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Cerrar sesión</span>
                </Button>
              </div>
            )}
          </div>
        </nav>
      </header>

      {/* ========================================================= */}
      {/* MOBILE HEADER: Clean Top Bar (visible on < 768px)         */}
      {/* ========================================================= */}
      <header className="flex md:hidden sticky top-0 z-30 h-14 w-full items-center justify-between border-b border-slate-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md px-4 transition-colors duration-200">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Stethoscope className="h-4 w-4" />
          </div>
          <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-zinc-100">
            Turnos Odontología
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {user && (
            <Badge variant="secondary" className="capitalize text-[10px] px-1.5 py-0.5">
              {ROLE_LABELS[user.rol]}
            </Badge>
          )}
          <ThemeToggle />
          {user && (
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-slate-500 hover:text-destructive active:scale-95 transition-transform"
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </header>

      {/* ========================================================= */}
      {/* MAIN CONTENT VIEW (Full width, safe bottom padding)       */}
      {/* ========================================================= */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 pb-28 md:pb-12 w-full max-w-6xl mx-auto">
        <Outlet />
      </main>

      {/* ========================================================= */}
      {/* MOBILE BOTTOM DOCK (visible on < 768px)                   */}
      {/* ========================================================= */}
      {allowedNavItems.length > 0 && (
        <div className="flex md:hidden fixed bottom-4 inset-x-4 z-40 justify-center pointer-events-none">
          <nav
            aria-label="Navegación móvil"
            className="glass-surface pointer-events-auto w-full max-w-md rounded-full p-1.5 flex items-center justify-around shadow-xl border border-white/40 dark:border-white/10"
          >
            {allowedNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      'relative min-h-[44px] min-w-[44px] flex flex-col items-center justify-center p-1.5 rounded-2xl transition-all duration-150 active:scale-[0.96]',
                      isActive
                        ? 'text-primary font-bold'
                        : 'text-slate-400 dark:text-zinc-500 hover:text-slate-700 dark:hover:text-zinc-300'
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute -top-3 w-8 h-8 rounded-full bg-primary text-primary-foreground shadow-md shadow-primary/40 flex items-center justify-center">
                          <Icon className="w-4 h-4" />
                        </span>
                      )}
                      <div className={cn(isActive && 'opacity-0')}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-medium mt-0.5">{item.label}</span>
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>
      )}

    </div>
  );
};

export default AppLayout;
