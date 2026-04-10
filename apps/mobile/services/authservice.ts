/**
 * Auth service re-exports for backwards compatibility.
 * Full authentication logic lives in `lib/api/auth.ts`.
 * The previous mockLogin function has been removed — use loginUser() instead.
 *
 * @module services/authservice
 */
export {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  loginWithGoogle,
  isAuthenticated,
} from '@/lib/api/auth';
