// Configuración de la aplicación
const BASE_URL = import.meta.env.VITE_API_URL;

export const API_CONFIG = {
  API_BASE_URL: BASE_URL,

  //endpoints
  WS_URL: BASE_URL.replace('http', 'ws') + '/video/ws/process_frame',
  RESET_COUNTER: '/video/reset_counter',
  PROCESS_VIDEO: '/video/process_video',
};

// Configuración de video
export const VIDEO_CONFIG = {
  width: 640,
  height: 480,
  fps: 10, // Frames por segundo para enviar al servidor
}

// Configuración de canvas
export const CANVAS_CONFIG = {
  lineWidth: 3,
  colors: {
    line: '#00FFFF',
    shoulder: '#00FFFF',
    elbow: '#FF00FF',
    wrist: '#FFFF00',
    text: 'white',
  },
  pointRadius: 8,
  fontSize: '20px',
  fontFamily: 'Arial',
}

// Estados de conexión
export const CONNECTION_STATUS = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error',
}

// Mensajes de estado
export const STATUS_MESSAGES = {
  [CONNECTION_STATUS.DISCONNECTED]: '🔴 Desconectado',
  [CONNECTION_STATUS.CONNECTING]: '🟡 Conectando...',
  [CONNECTION_STATUS.CONNECTED]: '🟢 Conectado - Procesando...',
  [CONNECTION_STATUS.ERROR]: '🔴 Error de conexión',
  CAMERA_ACTIVE: '🟡 Cámara activa - Listo para conectar',
}