import ENV from '@/lib/config/env';
import type { JabRealtimeFramePayload, JabRealtimeServerMessage } from '@/interfaces/interfaces';

const stripTrailingSlash = (value: string): string => value.replace(/\/+$/, '');

const toWebsocketScheme = (value: string): string => {
  if (value.startsWith('wss://') || value.startsWith('ws://')) {
    return value;
  }
  if (value.startsWith('https://')) {
    return value.replace('https://', 'wss://');
  }
  if (value.startsWith('http://')) {
    return value.replace('http://', 'ws://');
  }
  return `ws://${value}`;
};

const WS_BASE_URL = toWebsocketScheme(stripTrailingSlash(ENV.API_BASE_URL));

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface RealtimePoseServiceCallbacks {
  onStatusChange: (status: ConnectionStatus) => void;
  onFrame: (data: JabRealtimeFramePayload) => void;
  onError: (error: Error) => void;
}

class RealtimePoseService {
  private ws: WebSocket | null = null;
  private callbacks: RealtimePoseServiceCallbacks | null = null;
  private isProcessing = false;
  private pendingFrames = 0;
  private readonly MAX_PENDING_FRAMES = 2;

  connect(callbacks: RealtimePoseServiceCallbacks): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if (__DEV__) {
        console.log('[RealtimePoseService] WebSocket already connected');
      }
      return;
    }

    this.callbacks = callbacks;
    callbacks.onStatusChange('connecting');

    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/boxing/ws/jab`);

      this.ws.onopen = () => {
        if (__DEV__) {
          console.log('[RealtimePoseService] WebSocket connected');
        }
        callbacks.onStatusChange('connected');
        this.isProcessing = true;
        this.pendingFrames = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: JabRealtimeServerMessage = JSON.parse(event.data);

          if (parsed.error) {
            callbacks.onError(new Error(parsed.error));
            return;
          }

          callbacks.onFrame({
            frame: parsed.frame,
            feedback: parsed.feedback ?? null,
            jab_detected: parsed.jab_detected ?? false,
            frame_index: typeof parsed.frame_index === 'number' ? parsed.frame_index : null,
          });
        } catch (error) {
          if (__DEV__) {
            console.error('[RealtimePoseService] Error parsing WebSocket message', error);
          }
        } finally {
          if (this.pendingFrames > 0) {
            this.pendingFrames--;
          }
        }
      };

      this.ws.onerror = () => {
        if (__DEV__) {
          console.error('[RealtimePoseService] WebSocket error');
        }
        callbacks.onStatusChange('error');
        callbacks.onError(new Error('WebSocket connection failed'));
      };

      this.ws.onclose = () => {
        if (__DEV__) {
          console.log('[RealtimePoseService] WebSocket closed');
        }
        callbacks.onStatusChange('disconnected');
        this.isProcessing = false;
        this.pendingFrames = 0;
      };
    } catch (error) {
      if (__DEV__) {
        console.error('[RealtimePoseService] Failed to create WebSocket', error);
      }
      callbacks.onStatusChange('error');
      callbacks.onError(error as Error);
    }
  }

  sendFrame(base64Image: string, fps?: number): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (__DEV__) {
        console.warn('[RealtimePoseService] WebSocket not ready, skipping frame');
      }
      return false;
    }

    if (this.pendingFrames >= this.MAX_PENDING_FRAMES) {
      if (__DEV__) {
        console.warn('[RealtimePoseService] Backend overloaded, skipping frame');
      }
      return false;
    }

    try {
      const payload = JSON.stringify(
        typeof fps === 'number'
          ? { frame: base64Image, fps }
          : { frame: base64Image },
      );
      this.ws.send(payload);
      this.pendingFrames++;
      return true;
    } catch (error) {
      if (__DEV__) {
        console.error('[RealtimePoseService] Error sending frame', error);
      }
      this.callbacks?.onError(error as Error);
      return false;
    }
  }

  disconnect(): void {
    this.isProcessing = false;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.callbacks = null;
    this.pendingFrames = 0;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getIsProcessing(): boolean {
    return this.isProcessing;
  }

  getPendingFrames(): number {
    return this.pendingFrames;
  }

  requestReset(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    try {
      this.ws.send(JSON.stringify({ action: 'reset' }));
    } catch (error) {
      if (__DEV__) {
        console.error('[RealtimePoseService] Error sending reset command', error);
      }
      this.callbacks?.onError(error as Error);
    }
  }
}

export const realtimePoseService = new RealtimePoseService();
