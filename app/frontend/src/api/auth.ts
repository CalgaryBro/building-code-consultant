/**
 * Authentication API Client for Calgary Building Code Expert System
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_verified: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

export interface MessageResponse {
  message: string;
}

class AuthApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'AuthApiError';
    this.status = status;
  }
}

async function authRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}/auth${endpoint}`;

  const config: RequestInit = {
    ...options,
    credentials: 'include', // Include cookies for session management
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new AuthApiError(response.status, error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const authApi = {
  /**
   * Login with email and password
   */
  login: (credentials: LoginCredentials) => {
    return authRequest<AuthResponse>('/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  /**
   * Register a new user
   */
  register: (data: RegisterData) => {
    return authRequest<AuthResponse>('/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Logout the current user
   */
  logout: () => {
    return authRequest<MessageResponse>('/logout', {
      method: 'POST',
    });
  },

  /**
   * Get the current authenticated user
   */
  me: () => {
    return authRequest<User>('/me');
  },

  /**
   * Request a password reset email
   */
  forgotPassword: (email: string) => {
    return authRequest<MessageResponse>('/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  /**
   * Reset password with token
   */
  resetPassword: (token: string, password: string) => {
    return authRequest<MessageResponse>('/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    });
  },

  /**
   * Verify email with token
   */
  verifyEmail: (token: string) => {
    return authRequest<MessageResponse>('/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },

  /**
   * Resend verification email
   */
  resendVerification: () => {
    return authRequest<MessageResponse>('/resend-verification', {
      method: 'POST',
    });
  },
};

export { AuthApiError };
