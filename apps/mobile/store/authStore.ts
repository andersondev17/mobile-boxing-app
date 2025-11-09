/**
 * Authentication Store - Zustand
 * Global state management for authentication
 * Handles user state, tokens, and auth operations
 * @module store/authStore
 */

import {
  isAuthenticated,
  loginUser,
  loginWithGoogle,
  logoutUser,
  registerUser,
} from '@/lib/api/auth';
import type { ApiError, LoginCredentials, RegisterData, User } from '@/types/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

/**
 * Authentication state interface
 */
interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  signIn: (credentials: LoginCredentials) => Promise<void>;
  signUp: (data: RegisterData) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  initialize: () => Promise<void>;
  clearError: () => void;
}

/**
 * Global authentication store
 *
 * Features:
 * - Persisted state across app restarts
 * - Automatic token management
 * - Error handling
 * - Loading states
 *
 * @example
 * // In a component
 * const { signIn, user, isLoading, error } = useAuthStore();
 *
 * const handleLogin = async () => {
 *   await signIn({ email, password });
 *   if (user) router.replace('/');
 * };
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /**
       * Sign in with email and password
       */
      signIn: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });

        try {
          await loginUser(credentials);

          set({
            user: { email: credentials.email, name: credentials.email.split('@')[0] } as User,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage =
            (error as ApiError)?.detail || 'Credenciales inválidas';

          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Register new user
       */
      signUp: async (data: RegisterData) => {
        set({ isLoading: true, error: null });

        try {
          await registerUser(data);

          set({
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage =
            (error as ApiError)?.detail || 'Error al crear cuenta';

          set({
            isLoading: false,
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Sign in with Google OAuth
       */
      signInWithGoogle: async () => {
        set({ isLoading: true, error: null });

        try {
          const response = await loginWithGoogle();

          set({
            user: response.user || null,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage =
            (error as Error)?.message || 'Error al iniciar sesión con Google';

          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Sign out and clear all data
       */
      signOut: async () => {
        set({ isLoading: true });

        try {
          await logoutUser();

          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          console.error('Error during sign out:', error);
          // Still clear local state even if server request fails
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      /**
       * Initialize auth state on app start
       * Checks if user has valid tokens
       */
      initialize: async () => {
        const hasTokens = await isAuthenticated();

        if (!hasTokens) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          return;
        }

        // User has tokens - restore persisted staterefresh handled by apiClient
        set({ isLoading: false });
      },
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage', // AsyncStorage key
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist user data, not loading/error states
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Selector hooks for  performance
 */
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
