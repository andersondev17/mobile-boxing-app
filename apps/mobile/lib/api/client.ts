/**
 * API Client with automatic token refresh and request interceptors
 * Replicates axios interceptor behavior using native fetch
 * @module lib/api/client
 */

import ENV from '@/lib/config/env';
import type { ApiError } from '@/types/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Base API configuration
 * Automatically adjusts for iOS Simulator, Android Emulator, or production
 */
export const API_BASE_URL = ENV.API_BASE_URL;

/**
 * Storage keys for tokens
 */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
} as const;

/**
 * Request configuration options
 */
interface RequestConfig extends Omit<RequestInit, 'headers'> {
  _retry?: boolean;
  headers?: Record<string, string>;
}

/**
 * Get access token from AsyncStorage
 */
export const getAccessToken = async (): Promise<string | null> => {
  try {
    return await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  } catch (error) {
    console.error('Error getting access token:', error);
    return null;
  }
};

/**
 * Get refresh token from AsyncStorage
 */
export const getRefreshToken = async (): Promise<string | null> => {
  try {
    return await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (error) {
    console.error('Error getting refresh token:', error);
    return null;
  }
};

/**
 * Save tokens to AsyncStorage
 */
export const saveTokens = async (
  accessToken: string,
  refreshToken: string
): Promise<void> => {
  try {
    await AsyncStorage.multiSet([
      [STORAGE_KEYS.ACCESS_TOKEN, accessToken],
      [STORAGE_KEYS.REFRESH_TOKEN, refreshToken],
    ]);
  } catch (error) {
    console.error('Error saving tokens:', error);
    throw error;
  }
};

/**
 * Clear all tokens from AsyncStorage
 */
export const clearTokens = async (): Promise<void> => {
  try {
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
    ]);
  } catch (error) {
    console.error('Error clearing tokens:', error);
  }
};

/**
 * Refresh the access token using the refresh token
 * @returns {Promise<string>} New access token
 * @throws {Error} If refresh fails
 */
const refreshAccessToken = async (): Promise<string> => {
  const refreshToken = await getRefreshToken();

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    await clearTokens();
    throw new Error('Token refresh failed');
  }

  const data = await response.json();
  await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);

  return data.access_token;
};

/**
 * Enhanced fetch with automatic token injection and refresh
 * Mimics axios interceptor behavior:
 * 1. Automatically adds Authorization header
 * 2. Intercepts 401 errors
 * 3. Attempts token refresh
 * 4. Retries original request
 *
 * @param {string} url - API endpoint (relative or absolute)
 * @param {RequestConfig} config - Fetch configuration
 * @returns {Promise<Response>} Fetch response
 * @throws {Error} If request fails after retry
 *
 * @example
 * const response = await apiClient('/auth/me');
 * const user = await response.json();
 */
export const apiClient = async (
  url: string,
  config: RequestConfig = {}
): Promise<Response> => {
  // Build full URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  // Get access token and add to headers
  const accessToken = await getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(config.headers || {}),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Execute request
  try {
    let response = await fetch(fullUrl, {
      ...config,
      headers: headers as HeadersInit,
    });

    // Handle 401 Unauthorized - attempt token refresh
    if (response.status === 401 && !config._retry) {
      try {
        const newAccessToken = await refreshAccessToken();

        // Retry original request with new token
        const retryHeaders: Record<string, string> = {
          ...headers,
          'Authorization': `Bearer ${newAccessToken}`,
        };

        const { _retry, ...fetchConfig } = config;
        response = await fetch(fullUrl, {
          ...fetchConfig,
          headers: retryHeaders as HeadersInit,
        });
      } catch (refreshError) {
        await clearTokens();
        throw refreshError;
      }
    }

    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * Parse API response or throw typed error
 * @param {Response} response - Fetch response
 * @returns {Promise<T>} Parsed JSON data
 * @throws {ApiError} If response is not ok
 */
export const handleApiResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let errorMessage = 'An error occurred';

    try {
      const errorData: ApiError = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }

    const error: ApiError = {
      detail: errorMessage,
      status: response.status,
    };

    throw error;
  }

  return response.json();
};

/**
 * Convenience method: GET request
 */
export const get = async <T>(url: string, config?: RequestConfig): Promise<T> => {
  const response = await apiClient(url, { ...config, method: 'GET' });
  return handleApiResponse<T>(response);
};

/**
 * Convenience method: POST request 
 */
export const post = async <T>(
  url: string,
  data?: unknown,
  config?: RequestConfig
): Promise<T> => {
  const response = await apiClient(url, {
    ...config,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleApiResponse<T>(response);
};

/**
 * Convenience method: PUT request
 */
export const put = async <T>(
  url: string,
  data?: unknown,
  config?: RequestConfig
): Promise<T> => {
  const response = await apiClient(url, {
    ...config,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleApiResponse<T>(response);
};

/**
 * Convenience method: DELETE request
 */
export const del = async <T>(url: string, config?: RequestConfig): Promise<T> => {
  const response = await apiClient(url, { ...config, method: 'DELETE' });
  return handleApiResponse<T>(response);
};
