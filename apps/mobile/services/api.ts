/**
 * Thin re-export of the shared API client for backwards compatibility.
 * Prefer importing directly from `lib/api/client` in new code.
 *
 * @module services/api
 */
export { get, post, patch, del as delete } from '@/lib/api/client';
