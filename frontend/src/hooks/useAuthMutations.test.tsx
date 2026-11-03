import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { useLoginMutation, useChangePasswordMutation } from './useAuthMutations';
import * as authService from '@/services/authService';
import type { TokenResponsePayload } from '@/types/auth';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

describe('useAuthMutations (Strict TDD)', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('useLoginMutation successfully establishes session in AuthContext', async () => {
    const mockTokenResponse: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '5', rol: 'odontologo', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'odontologo',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    vi.spyOn(authService, 'loginUser').mockResolvedValueOnce(mockTokenResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => {
        const auth = useAuth();
        const loginMutation = useLoginMutation();
        return { auth, loginMutation };
      },
      { wrapper }
    );

    expect(result.current.auth.user).toBeNull();

    result.current.loginMutation.mutate({
      payload: { identificador: 'carlos@clinica.com', password: 'Password1' },
      remember: true,
    });

    await waitFor(() => expect(result.current.loginMutation.isSuccess).toBe(true));

    expect(result.current.auth.user?.rol).toBe('odontologo');
    expect(result.current.auth.user?.debe_cambiar_password).toBe(false);
  });

  it('useChangePasswordMutation updates user session with updated token response', async () => {
    const mockChangeResponse: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '12', rol: 'paciente', debe_cambiar_password: false })) + '.sig',
      token_type: 'bearer',
      rol: 'paciente',
      debe_cambiar_password: false,
      perfil_completo: true,
    };

    vi.spyOn(authService, 'changePassword').mockResolvedValueOnce(mockChangeResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => {
        const auth = useAuth();
        const changeMutation = useChangePasswordMutation();
        return { auth, changeMutation };
      },
      { wrapper }
    );

    result.current.changeMutation.mutate({
      password_actual: 'OldPass123',
      password_nueva: 'NewPass456',
    });

    await waitFor(() => expect(result.current.changeMutation.isSuccess).toBe(true));

    expect(result.current.auth.user?.rol).toBe('paciente');
    expect(result.current.auth.user?.debe_cambiar_password).toBe(false);
  });
});
