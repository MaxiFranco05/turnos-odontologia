import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios';

const TOKEN_KEY = 'auth_token';

interface ErrorResponseData {
  detail?: string;
  code?: string;
}

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string, remember: boolean = true): void {
  try {
    if (remember) {
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
      sessionStorage.setItem(TOKEN_KEY, token);
    }
  } catch {
    // LocalStorage or sessionStorage might be restricted
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // LocalStorage or sessionStorage might be restricted
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request Interceptor: Injects Bearer token if present
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error)
);

// Response Interceptor setup
let unauthorizedHandler: (() => void) | undefined;
let forbiddenHandler: (() => void) | undefined;
let passwordChangeRequiredHandler: (() => void) | undefined;

export function setupResponseInterceptors(
  onUnauthorized?: () => void,
  onForbidden?: () => void,
  onPasswordChangeRequired?: () => void
): void {
  unauthorizedHandler = onUnauthorized;
  forbiddenHandler = onForbidden;
  passwordChangeRequiredHandler = onPasswordChangeRequired;
}

export function setPasswordChangeRequiredHandler(handler?: () => void): void {
  passwordChangeRequiredHandler = handler;
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ErrorResponseData>) => {
    if (error.response) {
      const { status, data } = error.response;
      const isPasswordChangeRequired =
        (status === 403 || status === 400) &&
        (data?.detail === 'password_change_required' || data?.code === 'password_change_required');

      if (status === 401) {
        clearAuthToken();
        if (unauthorizedHandler) {
          unauthorizedHandler();
        } else if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      } else if (isPasswordChangeRequired) {
        if (passwordChangeRequiredHandler) {
          passwordChangeRequiredHandler();
        } else if (typeof window !== 'undefined' && window.location.pathname !== '/cambiar-password') {
          window.location.href = '/cambiar-password';
        }
      } else if (status === 403) {
        if (forbiddenHandler) {
          forbiddenHandler();
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
