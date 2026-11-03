import { useMutation } from '@tanstack/react-query';
import { useAuth } from '@/context/AuthContext';
import { loginUser, changePassword } from '@/services/authService';
import type { LoginRequestPayload, ChangePasswordRequestPayload, TokenResponsePayload } from '@/types/auth';

export interface LoginMutationVariables {
  payload: LoginRequestPayload;
  remember?: boolean;
}

/**
 * Mutation hook for user authentication against POST /api/auth/login.
 * Avoids useEffect per Hard Rule #6 and automatically syncs AuthContext session.
 */
export function useLoginMutation() {
  const { establishSession } = useAuth();

  return useMutation<TokenResponsePayload, Error, LoginMutationVariables>({
    mutationFn: ({ payload }) => loginUser(payload),
    onSuccess: (data, variables) => {
      establishSession(data, variables.payload.identificador, variables.remember ?? true);
    },
  });
}

/**
 * Mutation hook for mandatory password update against POST /api/auth/cambiar-password.
 * Replaces active session credentials with updated JWT token upon completion.
 */
export function useChangePasswordMutation() {
  const { establishSession, user } = useAuth();

  return useMutation<TokenResponsePayload, Error, ChangePasswordRequestPayload>({
    mutationFn: (payload) => changePassword(payload),
    onSuccess: (data) => {
      establishSession(data, user?.email || user?.identificador, true);
    },
  });
}
