import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { router } from '@/router/routes';
import { DevToolbar } from '@/components/DevToolbar';

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <RouterProvider router={router} />
          {import.meta.env.DEV && <DevToolbar />}
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
