import { createBrowserRouter, Navigate } from 'react-router-dom';
import AuthLayout from '@/layouts/AuthLayout';
import AppLayout from '@/layouts/AppLayout';
import ProtectedRoute from './ProtectedRoute';
import LoginPage from '@/pages/LoginPage';
import CambiarPasswordPage from '@/pages/CambiarPasswordPage';

export const router = createBrowserRouter([
  // Public authentication & mandatory password change routes (C-04 / C-12)
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/login" replace />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'cambiar-password',
        element: <CambiarPasswordPage />,
      },
    ],
  },

  // Protected application routes by role (C-13, C-14, C-15)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          // Recepción (C-14)
          {
            path: 'recepcion/agenda',
            element: (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">Agenda del Día (Recepción)</h2>
                <p className="mt-2 text-slate-600">
                  Módulo de confirmación y anulación de turnos diarios (a implementar en C-14).
                </p>
              </div>
            ),
          },
          {
            path: 'recepcion/plantillas',
            element: (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">Plantillas de Disponibilidad</h2>
                <p className="mt-2 text-slate-600">
                  Módulo de configuración de horarios por odontólogo (a implementar en C-14).
                </p>
              </div>
            ),
          },
          // Odontólogo (C-15)
          {
            path: 'odontologo/agenda',
            element: (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">Mi Agenda (Odontólogo)</h2>
                <p className="mt-2 text-slate-600">
                  Módulo de turnos del día y marcado de presente/ausente (a implementar en C-15).
                </p>
              </div>
            ),
          },
          // Paciente (C-13)
          {
            path: 'paciente/disponibilidad',
            element: (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">Reserva de Turnos (Paciente)</h2>
                <p className="mt-2 text-slate-600">
                  Módulo de búsqueda de huecos disponibles y solicitud online (a implementar en C-13).
                </p>
              </div>
            ),
          },
          {
            path: 'paciente/mis-turnos',
            element: (
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-bold text-slate-900">Mis Turnos (Paciente)</h2>
                <p className="mt-2 text-slate-600">
                  Módulo de historial y cancelación con anticipación mínima (a implementar en C-13).
                </p>
              </div>
            ),
          },
        ],
      },
    ],
  },

  // Catch-all fallback
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);

export function createAppRouter() {
  return router;
}

export default router;
