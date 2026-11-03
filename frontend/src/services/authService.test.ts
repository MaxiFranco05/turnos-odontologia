import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  loginUser,
  changePassword,
  decodeJwtPayload,
  saveAuthSession,
  loadAuthSession,
  clearAuthSession,
} from './authService';
import apiClient, { getAuthToken, setAuthToken, clearAuthToken } from '@/lib/api';
import type { TokenResponsePayload, LoginRequestPayload, ChangePasswordRequestPayload } from '@/types/auth';

describe('authService & session management (Strict TDD)', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  describe('decodeJwtPayload', () => {
    it('decodes a valid JWT base64url payload with sub, rol, and debe_cambiar_password', () => {
      // payload: {"sub":"42","rol":"odontologo","debe_cambiar_password":false,"exp":1999999999}
      const rawPayload = JSON.stringify({
        sub: '42',
        rol: 'odontologo',
        debe_cambiar_password: false,
        exp: 1999999999,
      });
      const b64 = btoa(rawPayload).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const fakeToken = `eyJhbGciOiJIUzI1NiJ9.${b64}.signature`;

      const claims = decodeJwtPayload(fakeToken);
      expect(claims).not.toBeNull();
      expect(claims?.sub).toBe('42');
      expect(claims?.rol).toBe('odontologo');
      expect(claims?.debe_cambiar_password).toBe(false);
    });

    it('returns null when given a malformed or empty token', () => {
      expect(decodeJwtPayload('')).toBeNull();
      expect(decodeJwtPayload('invalid-single-segment')).toBeNull();
      expect(decodeJwtPayload('not.valid-base64.token')).toBeNull();
    });
  });

  describe('loginUser API call', () => {
    it('sends POST /auth/login with exact payload and returns TokenResponse', async () => {
      const mockResponse: TokenResponsePayload = {
        access_token: 'valid.token.recepcion',
        token_type: 'bearer',
        rol: 'recepcion',
        debe_cambiar_password: false,
        perfil_completo: true,
      };

      const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const payload: LoginRequestPayload = {
        identificador: 'recepcion@clinica.com',
        password: 'Password123',
      };

      const result = await loginUser(payload);
      expect(postSpy).toHaveBeenCalledWith('/auth/login', payload);
      expect(result).toEqual(mockResponse);
    });

    it('propagates error when login fails (e.g. 401)', async () => {
      vi.spyOn(apiClient, 'post').mockRejectedValueOnce(new Error('Credenciales inválidas'));

      await expect(
        loginUser({ identificador: 'wrong@clinica.com', password: 'bad' })
      ).rejects.toThrow('Credenciales inválidas');
    });
  });

  describe('changePassword API call', () => {
    it('sends POST /auth/cambiar-password with exact payload without extra forbidden fields', async () => {
      const mockResponse: TokenResponsePayload = {
        access_token: 'new.token.fresh',
        token_type: 'bearer',
        rol: 'paciente',
        debe_cambiar_password: false,
        perfil_completo: true,
      };

      const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const payload: ChangePasswordRequestPayload = {
        password_actual: 'TempPass1',
        password_nueva: 'SecurePass99',
        nombre: 'Lucía',
        email: 'lucia@gmail.com',
      };

      const result = await changePassword(payload);
      expect(postSpy).toHaveBeenCalledWith('/auth/cambiar-password', payload);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Storage persistence & session hydration (remember vs ephemeral)', () => {
    const sampleTokenResponse: TokenResponsePayload = {
      access_token: 'header.' + btoa(JSON.stringify({ sub: '10', rol: 'paciente', debe_cambiar_password: true })) + '.sig',
      token_type: 'bearer',
      rol: 'paciente',
      debe_cambiar_password: true,
      perfil_completo: false,
    };

    it('persists session in localStorage when remember=true', () => {
      saveAuthSession(sampleTokenResponse, true, 'socio123');

      expect(localStorage.getItem('auth_token')).toBe(sampleTokenResponse.access_token);
      expect(sessionStorage.getItem('auth_token')).toBeNull();

      const hydrated = loadAuthSession();
      expect(hydrated).not.toBeNull();
      expect(hydrated?.token).toBe(sampleTokenResponse.access_token);
      expect(hydrated?.user.rol).toBe('paciente');
      expect(hydrated?.user.debe_cambiar_password).toBe(true);
      expect(hydrated?.user.perfil_completo).toBe(false);
    });

    it('persists session in sessionStorage when remember=false', () => {
      saveAuthSession(sampleTokenResponse, false, 'socio123');

      expect(sessionStorage.getItem('auth_token')).toBe(sampleTokenResponse.access_token);
      expect(localStorage.getItem('auth_token')).toBeNull();

      const hydrated = loadAuthSession();
      expect(hydrated).not.toBeNull();
      expect(hydrated?.token).toBe(sampleTokenResponse.access_token);
    });

    it('clears both storages on clearAuthSession()', () => {
      saveAuthSession(sampleTokenResponse, true, 'socio123');
      expect(loadAuthSession()).not.toBeNull();

      clearAuthSession();
      expect(loadAuthSession()).toBeNull();
      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(sessionStorage.getItem('auth_token')).toBeNull();
    });
  });
});
