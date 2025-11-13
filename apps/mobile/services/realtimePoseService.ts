import type { CVPipelineResponse } from '@/interfaces/interfaces';

const getApiUrl = (): string => {
  const env = process.env.EXPO_PUBLIC_ENV || 'development';

  if (env === 'development') {
    const ip = process.env.EXPO_PUBLIC_LOCAL_IP || '192.168.1.26';
    const port = process.env.EXPO_PUBLIC_BACKEND_PORT || '8000';
    return `ws://${ip}:${port}`;
  }

  const apiUrl = process.env.EXPO_PUBLIC_API_URL || '';
  return apiUrl.replace('https://', 'wss://').replace('http://', 'ws://');
};

const WS_BASE_URL = getApiUrl();

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface RealtimePoseServiceCallbacks {
  onStatusChange: (status: ConnectionStatus) => void;
  onPoseUpdate: (data: CVPipelineResponse) => void;
  onError: (error: Error) => void;
}

class RealtimePoseService {
  private ws: WebSocket | null = null;
  private callbacks: RealtimePoseServiceCallbacks | null = null;
  private isProcessing = false;
  private pendingFrames = 0;
  private readonly MAX_PENDING_FRAMES = 2;

  /**
   * Connects to the backend WebSocket
   */
  connect(callbacks: RealtimePoseServiceCallbacks): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if (__DEV__) {
        console.log('⚠️ WebSocket already connected');
      }
      return;
    }

    this.callbacks = callbacks;
    callbacks.onStatusChange('connecting');

    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/video/ws/process_frame`);

      this.ws.onopen = () => {
        if (__DEV__) {
          console.log('✅ WebSocket connected');
        }
        callbacks.onStatusChange('connected');
        this.isProcessing = true;
        this.pendingFrames = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: CVPipelineResponse = JSON.parse(event.data);
          callbacks.onPoseUpdate(data);

          // Decrease pending frames counter (backpressure control)
          if (this.pendingFrames > 0) {
            this.pendingFrames--;
          }
        } catch (error) {
          if (__DEV__) {
            console.error('❌ Error parsing WebSocket message:', error);
          }
        }
      };

      this.ws.onerror = (error) => {
        if (__DEV__) {
          console.error('❌ WebSocket error:', error);
        }
        callbacks.onStatusChange('error');
        callbacks.onError(new Error('WebSocket connection failed'));
      };

      this.ws.onclose = () => {
        if (__DEV__) {
          console.log('🔌 WebSocket closed');
        }
        callbacks.onStatusChange('disconnected');
        this.isProcessing = false;
        this.pendingFrames = 0;
      };
    } catch (error) {
      if (__DEV__) {
        console.error('❌ Failed to create WebSocket:', error);
      }
      callbacks.onStatusChange('error');
      callbacks.onError(error as Error);
    }
  }

  /**
   * Sends a frame (base64) to the server for processing
   * Implements backpressure to avoid overwhelming the backend
   */
  sendFrame(base64Image: string): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (__DEV__) {
        console.warn('⚠️ WebSocket not ready, skipping frame');
      }
      return false;
    }

    // Backpressure: don't send if backend is behind
    if (this.pendingFrames >= this.MAX_PENDING_FRAMES) {
      if (__DEV__) {
        console.warn('⚠️ Backend overloaded, skipping frame');
      }
      return false;
    }

    try {
      this.ws.send(base64Image);
      this.pendingFrames++;
      return true;
    } catch (error) {
      if (__DEV__) {
        console.error('❌ Error sending frame:', error);
      }
      this.callbacks?.onError(error as Error);
      return false;
    }
  }

  /**
   * Disconnects the WebSocket
   */
  disconnect(): void {
    this.isProcessing = false;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.callbacks = null;
    this.pendingFrames = 0;
  }

  /**
   * Checks if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Checks if actively processing frames
   */
  getIsProcessing(): boolean {
    return this.isProcessing;
  }

  /**
   * Gets current backpressure level (0-MAX_PENDING_FRAMES)
   */
  getPendingFrames(): number {
    return this.pendingFrames;
  }
}

export const realtimePoseService = new RealtimePoseService();
