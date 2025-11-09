// Environment configuration
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const isDev = __DEV__;

const ENV_NAME = process.env.EXPO_PUBLIC_ENV || (isDev ? 'development' : 'production');
const getApiBaseUrl = (): string => {

  if (isDev) {
    // Get configuration from environment variables
    const localIp = process.env.EXPO_PUBLIC_LOCAL_IP;
    const port = process.env.EXPO_PUBLIC_BACKEND_PORT || '8000';

    // Priority 1: Use explicit API_URL if set
    if (process.env.EXPO_PUBLIC_API_URL) {
      return process.env.EXPO_PUBLIC_API_URL;
    }

    // Priority 2: Use LOCAL_IP for physical devices
    if (localIp) {
      return `http://${localIp}:${port}`;
    }

    // Priority 3: Auto-detect based on platform
    if (Platform.OS === 'android') {
      return `http://10.0.2.2:${port}`; // Android Emulator
    }
    return `http://localhost:${port}`; // iOS Simulator / Web
  }

  // Production: Use environment variable or fail-safe
  return process.env.EXPO_PUBLIC_API_URL ||
         Constants.expoConfig?.extra?.apiUrl ||
         'https://api.yourdomain.com';
};

// OAuth Configuration
const getOAuthConfig = () => {
  const clientId = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID;

  const redirectUri = process.env.EXPO_PUBLIC_GOOGLE_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    throw new Error(
      'Missing OAuth configuration. Set EXPO_PUBLIC_GOOGLE_CLIENT_ID and EXPO_PUBLIC_GOOGLE_REDIRECT_URI'
    );
  }

  return { clientId, redirectUri };
};

const oauthConfig = getOAuthConfig();

// Environment configuration

export const ENV = {
  API_BASE_URL: getApiBaseUrl(),
  IS_DEV: ENV_NAME === 'development',
  APP_VERSION: Constants.expoConfig?.version || '1.0.0',
  PLATFORM: Platform.OS,
  GOOGLE_CLIENT_ID: oauthConfig.clientId,
  GOOGLE_REDIRECT_URI: oauthConfig.redirectUri,
} as const;

export default ENV;
