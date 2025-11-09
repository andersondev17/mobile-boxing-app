/**
 * Authentication types for FastAPI backend integration
 * @module types/auth
 */

export interface User {
  id: string;
  name: string;
  email: string;
  picture?: string;
  provider?: 'email' | 'google';
  created_at?: string;
  updated_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

/**
 * Complete auth response (login/register)
 */
export interface AuthResponse extends AuthTokens {
  user?: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}
