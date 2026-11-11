import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { SimulatorProvider } from '@/context/SimulatorContext';
import { router } from '@/router/routes';
import { DevToolbar } from '@/components/DevToolbar';
import { PhoneSimulatorModal } from '@/components/PhoneSimulatorModal';

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <SimulatorProvider>
            <RouterProvider router={router} />
            {import.meta.env.DEV && <DevToolbar />}
            <PhoneSimulatorModal />
          </SimulatorProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
