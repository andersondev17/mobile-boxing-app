/**
 * PKCE (Proof Key for Code Exchange) Utilities
 *
 * Implements RFC 7636 for OAuth 2.0 public clients
 * Required by Google OAuth2 policies for mobile apps
 *
 * @module lib/utils/pkce
 */

import * as Crypto from 'expo-crypto';

/**
 * Generate a cryptographically random code verifier
 * @returns {Promise<string>} Random code verifier string
 */
export async function generateCodeVerifier(): Promise<string> {
  const randomBytes = await Crypto.getRandomBytesAsync(32);
  return base64URLEncode(randomBytes);
}

/**
 * Generate code challenge from code verifier using S256 method
 *
 * code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))
 *
 * @param {string} codeVerifier - The code verifier to hash
 * @returns {Promise<string>} Base64URL encoded SHA256 hash
 */
export async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  const hash = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    codeVerifier,
    {
      encoding: Crypto.CryptoEncoding.BASE64,
    }
  );

  // Convert base64 to base64url
  return base64URLEncode(hash);
}

/**
 * Generate a random state parameter for CSRF protection
 *
 * @returns {Promise<string>} Random state string
 */
export async function generateState(): Promise<string> {
  const randomBytes = await Crypto.getRandomBytesAsync(16);
  return base64URLEncode(randomBytes);
}

/**
 * Convert string or ArrayBuffer to base64url encoding
 *
 * Base64URL encoding replaces:
 * - '+' with '-'
 * - '/' with '_'
 * - Removes '=' padding
 *
 * @param {string | Uint8Array} input - Input to encode
 * @returns {string} Base64URL encoded string
 */
function base64URLEncode(input: string | Uint8Array): string {
  let base64: string;

  if (typeof input === 'string') {
    // If already base64, convert to base64url
    base64 = input;
  } else {
    // Convert Uint8Array to base64 using btoa() (React Native compatible)
    // Source: https://docs.expo.dev/versions/latest/sdk/crypto/
    const binaryString = String.fromCharCode(...Array.from(input));
    base64 = btoa(binaryString);
  }

  // Convert base64 to base64url (RFC 4648 §5)
  return base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

/**
 * PKCE Session Storage
 * Temporary storage for PKCE parameters during OAuth flow
 */
interface PKCESession {
  codeVerifier: string;
  codeChallenge: string;
  state: string;
  timestamp: number;
}

let currentPKCESession: PKCESession | null = null;

/**
 * Create and store a new PKCE session
 *
 * @returns {Promise<PKCESession>} New PKCE session with verifier, challenge, and state
 */
export async function createPKCESession(): Promise<PKCESession> {
  const codeVerifier = await generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  const state = await generateState();

  currentPKCESession = {
    codeVerifier,
    codeChallenge,
    state,
    timestamp: Date.now(),
  };

  return currentPKCESession;
}

/**
 * Retrieve and clear the current PKCE session
 *
 * @param {string} state - State parameter to validate
 * @returns {PKCESession | null} PKCE session if state matches, null otherwise
 * @throws {Error} If state doesn't match or session expired
 */
export function consumePKCESession(state: string): PKCESession | null {
  if (!currentPKCESession) {
    throw new Error('No PKCE session found');
  }

  if (currentPKCESession.state !== state) {
    currentPKCESession = null;
    throw new Error('State parameter mismatch - possible CSRF attack');
  }

  const session = currentPKCESession;
  currentPKCESession = null;
  return session;
}

/**
 * Clear the current PKCE session
 */
export function clearPKCESession(): void {
  currentPKCESession = null;
}
