import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios';

const TOKEN_KEY = 'auth_token';

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // LocalStorage might be restricted
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // LocalStorage might be restricted
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

export function setupResponseInterceptors(
  onUnauthorized?: () => void,
  onForbidden?: () => void
): void {
  unauthorizedHandler = onUnauthorized;
  forbiddenHandler = onForbidden;
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      if (error.response.status === 401) {
        clearAuthToken();
        if (unauthorizedHandler) {
          unauthorizedHandler();
        } else if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      } else if (error.response.status === 403) {
        if (forbiddenHandler) {
          forbiddenHandler();
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
