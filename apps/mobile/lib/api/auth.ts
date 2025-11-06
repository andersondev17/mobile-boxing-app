/**
 * Authentication API functions
 * Handles login, register, Google OAuth, and user management
 * @module lib/api/auth
 */

import * as WebBrowser from 'expo-web-browser';
import type {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  User,
} from '@/types/auth';
import { API_BASE_URL, apiClient, clearTokens, get, handleApiResponse, post, saveTokens } from './client';

/**
 * Register a new user with email and password
 *
 * @param {RegisterData} data - User registration data
 * @returns {Promise<AuthResponse>} Auth tokens and user data
 * @throws {ApiError} If registration fails
 *
 * @example
 * const response = await registerUser({
 *   name: 'John Doe',
 *   email: 'john@example.com',
 *   password: 'securepass123'
 * });
 */
export const registerUser = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await post<AuthResponse>('/auth/register', data);

  // Save tokens to AsyncStorage
  if (response.access_token && response.refresh_token) {
    await saveTokens(response.access_token, response.refresh_token);
  }

  return response;
};

/**
 * Login user with email and password
 *
 * @param {LoginCredentials} credentials - User login credentials
 * @returns {Promise<AuthResponse>} Auth tokens and user data
 * @throws {ApiError} If login fails
 *
 * @example
 * const response = await loginUser({
 *   email: 'john@example.com',
 *   password: 'securepass123'
 * });
 */
export const loginUser = async (
  credentials: LoginCredentials
): Promise<AuthResponse> => {
  // Backend expects OAuth2PasswordRequestForm (form-urlencoded)
  // Convert JSON to URLSearchParams
  const formData = new URLSearchParams();
  formData.append('username', credentials.email); // Backend uses 'username' field
  formData.append('password', credentials.password);

  const response = await apiClient('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  const data = await handleApiResponse<AuthResponse>(response);

  // Save tokens to AsyncStorage
  if (data.access_token && data.refresh_token) {
    await saveTokens(data.access_token, data.refresh_token);
  }

  return data;
};

/**
 * Login with Google OAuth2
 * Opens browser for Google authentication flow
 *
 * @returns {Promise<AuthResponse>} Auth tokens and user data
 * @throws {Error} If Google login fails or is cancelled
 *
 * @example
 * try {
 *   const response = await loginWithGoogle();
 *   console.log('Logged in:', response.user);
 * } catch (error) {
 *   console.error('Google login failed:', error);
 * }
 */
export const loginWithGoogle = async (): Promise<AuthResponse> => {
  try {
    // Open Google OAuth flow in browser
    const authUrl = `${API_BASE_URL}/auth/login/google`;

    const result = await WebBrowser.openAuthSessionAsync(
      authUrl,
      `${API_BASE_URL}/auth/callback` // Redirect URL after auth
    );

    if (result.type === 'cancel') {
      throw new Error('Google login cancelled by user');
    }

    if (result.type !== 'success' || !result.url) {
      throw new Error('Google login failed');
    }

    // Parse tokens from callback URL
    const url = new URL(result.url);
    const accessToken = url.searchParams.get('access_token');
    const refreshToken = url.searchParams.get('refresh_token');

    if (!accessToken || !refreshToken) {
      throw new Error('No tokens received from Google login');
    }

    // Save tokens
    await saveTokens(accessToken, refreshToken);

    // Fetch user data
    const user = await getCurrentUser();

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      user,
    };
  } catch (error) {
    console.error('Google login error:', error);
    throw error;
  }
};

/**
 * Get current authenticated user
 *
 * @returns {Promise<User>} Current user data
 * @throws {ApiError} If not authenticated or request fails
 *
 * @example
 * const user = await getCurrentUser();
 * console.log('Current user:', user.name);
 */
export const getCurrentUser = async (): Promise<User> => {
  return get<User>('/auth/me');
};

/**
 * Refresh access token using refresh token
 * Note: This is handled automatically by the API client
 * This function is exposed for manual token refresh if needed
 *
 * @param {string} refreshToken - Refresh token
 * @returns {Promise<{access_token: string}>} New access token
 * @throws {ApiError} If refresh fails
 */
export const refreshToken = async (
  refreshToken: string
): Promise<{ access_token: string }> => {
  const response = await post<{ access_token: string }>('/auth/refresh', {
    refresh_token: refreshToken,
  });

  // Update stored access token
  if (response.access_token) {
    const { STORAGE_KEYS } = await import('./client');
    const AsyncStorage = (await import('@react-native-async-storage/async-storage'))
      .default;
    await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
  }

  return response;
};

/**
 * Logout user and clear all tokens
 *
 * @returns {Promise<void>}
 *
 * @example
 * await logoutUser();
 * router.replace('/sign-in');
 */
export const logoutUser = async (): Promise<void> => {
  await clearTokens();
};

/**
 * Check if user is authenticated (has valid tokens)
 *
 * @returns {Promise<boolean>} True if tokens exist
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const { getAccessToken } = await import('./client');
  const token = await getAccessToken();
  return !!token;
};
