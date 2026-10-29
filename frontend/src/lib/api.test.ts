import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import axios from 'axios';
import { apiClient, setAuthToken, clearAuthToken, getAuthToken, setupResponseInterceptors } from './api';

describe('API Client & Networking (Strict TDD)', () => {
  beforeEach(() => {
    localStorage.clear();
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
  });
});
