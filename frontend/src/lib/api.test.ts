import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiClient, setAuthToken, clearAuthToken, getAuthToken, setupResponseInterceptors } from './api';

describe('API Client & Networking (Strict TDD)', () => {
  beforeEach(() => {
    localStorage.clear();
    setupResponseInterceptors(undefined, undefined, undefined);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('JWT Request Interceptor', () => {
    it('attaches Authorization header with Bearer token when token is present', async () => {
      setAuthToken('mock-jwt-token-xyz');
      expect(getAuthToken()).toBe('mock-jwt-token-xyz');

      // Intercept axios internal request handler
      const config = { headers: {} as Record<string, string> };
      // @ts-expect-error accessing internal interceptor handler for unit test
      const handledConfig = apiClient.interceptors.request.handlers[0].fulfilled(config);

      expect(handledConfig.headers.Authorization).toBe('Bearer mock-jwt-token-xyz');
    });

    it('does not attach Authorization header when token is absent', async () => {
      clearAuthToken();
      expect(getAuthToken()).toBeNull();

      const config = { headers: {} as Record<string, string> };
      // @ts-expect-error accessing internal interceptor handler for unit test
      const handledConfig = apiClient.interceptors.request.handlers[0].fulfilled(config);

      expect(handledConfig.headers.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor & Session Expiration (401 / 403)', () => {
    it('clears token and invokes onUnauthorized callback on 401 error', async () => {
      setAuthToken('expired-token');
      const onUnauthorized = vi.fn();
      setupResponseInterceptors(onUnauthorized);

      const error = {
        response: { status: 401, data: { detail: 'Token expired' } },
        isAxiosError: true,
      };

      // @ts-expect-error accessing internal response error interceptor handler
      const errorInterceptor = apiClient.interceptors.response.handlers[apiClient.interceptors.response.handlers.length - 1].rejected;

      await expect(errorInterceptor(error)).rejects.toEqual(error);
      expect(getAuthToken()).toBeNull();
      expect(onUnauthorized).toHaveBeenCalledTimes(1);
    });

    it('invokes onForbidden callback on 403 error without clearing session token', async () => {
      setAuthToken('valid-patient-token');
      const onForbidden = vi.fn();
      setupResponseInterceptors(undefined, onForbidden);

      const error = {
        response: { status: 403, data: { detail: 'Acceso no autorizado al recurso' } },
        isAxiosError: true,
      };

      // @ts-expect-error accessing internal response error interceptor handler
      const errorInterceptor = apiClient.interceptors.response.handlers[apiClient.interceptors.response.handlers.length - 1].rejected;

      await expect(errorInterceptor(error)).rejects.toEqual(error);
      expect(getAuthToken()).toBe('valid-patient-token');
      expect(onForbidden).toHaveBeenCalledTimes(1);
    });

    it('passes through successful response data cleanly', async () => {
      const response = { status: 200, data: { ok: true } };
      // @ts-expect-error accessing internal response interceptor handler
      const responseInterceptor = apiClient.interceptors.response.handlers[0].fulfilled;

      const result = responseInterceptor(response);
      expect(result).toBe(response);
    });

    it('preserves JWT token and invokes passwordChangeRequiredHandler on 403/400 password_change_required without calling onForbidden', async () => {
      setAuthToken('temp-password-token');
      const onUnauthorized = vi.fn();
      const onForbidden = vi.fn();
      const onPasswordChangeRequired = vi.fn();
      setupResponseInterceptors(onUnauthorized, onForbidden, onPasswordChangeRequired);

      const error403 = {
        response: { status: 403, data: { detail: 'password_change_required' } },
        isAxiosError: true,
      };
      const error400 = {
        response: { status: 400, data: { detail: 'password_change_required' } },
        isAxiosError: true,
      };

      // @ts-expect-error accessing internal response error interceptor handler
      const errorInterceptor = apiClient.interceptors.response.handlers[apiClient.interceptors.response.handlers.length - 1].rejected;

      await expect(errorInterceptor(error403)).rejects.toEqual(error403);
      expect(getAuthToken()).toBe('temp-password-token');
      expect(onPasswordChangeRequired).toHaveBeenCalledTimes(1);
      expect(onForbidden).not.toHaveBeenCalled();
      expect(onUnauthorized).not.toHaveBeenCalled();

      await expect(errorInterceptor(error400)).rejects.toEqual(error400);
      expect(getAuthToken()).toBe('temp-password-token');
      expect(onPasswordChangeRequired).toHaveBeenCalledTimes(2);
      expect(onForbidden).not.toHaveBeenCalled();
    });
  });
});
