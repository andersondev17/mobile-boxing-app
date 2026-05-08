/**
 * RealtimePoseService
 * WebSocket client for real-time jab analysis.
 *
 * SEND format (mobile → backend):
 *   { landmarks: Array<{x,y,z}>, fps: 30, frame_index: number, user_id?, session_id? }
 *
 * RECEIVE format (backend → mobile):
 *   { feedback, jab_detected, frame_index, tracking_state, session_id? }
 *
 * Restriction C-01: NEVER send base64 or raw image bytes.
 * @module services/realtimePoseService
 */

import ENV from '@/lib/config/env';
import type { JabRealtimeServerMessage, LandmarkPoint } from '@/interfaces/interfaces';

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

/** WebSocket connection lifecycle states. */
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * Callbacks provided to {@link RealtimePoseService.connect}.
 * Use `onPoseUpdate` to receive processed server messages.
 */
export interface RealtimePoseServiceCallbacks {
  /** Called whenever the WebSocket connection state changes. */
  onStatusChange: (status: ConnectionStatus) => void;
  /**
   * Called for every processed server message.
   * Receives the full parsed {@link JabRealtimeServerMessage}.
   */
  onPoseUpdate: (data: JabRealtimeServerMessage) => void;
  /** Called on WebSocket errors or JSON parse failures. */
  onError: (error: Error) => void;
}

/**
 * Payload sent from mobile to the backend WebSocket.
 * All 33 MediaPipe pose landmarks must be present.
 */
export interface LandmarkPayload {
  /** 33 normalised pose landmarks [[x, y, z]] in MediaPipe order. */
  landmarks: LandmarkPoint[];
  /** Target frames-per-second — always 30. */
  fps: number;
  /** Zero-based monotonic counter for the current session. */
  frame_index: number;
  /** Optional authenticated user identifier. */
  user_id?: string;
  /** Optional session identifier returned by the backend. */
  session_id?: string;
}

class RealtimePoseService {
  private ws: WebSocket | null = null;
  private callbacks: RealtimePoseServiceCallbacks | null = null;
  private isProcessing = false;
  private pendingFrames = 0;
  private readonly MAX_PENDING_FRAMES = 2;
  /** True when the backend has asked us to slow down frame transmission. */
  private isSlowed = false;

  /**
   * Open the WebSocket and register lifecycle callbacks.
   * A no-op if the socket is already open.
   *
   * @param callbacks - Handlers for status, pose updates and errors.
   */
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
          const parsed = JSON.parse(event.data as string) as Record<string, unknown>;

          // ── Backpressure signals — handle locally, never forward to UI ──
          if (parsed.type === 'slow_down') {
            this.isSlowed = true;
            if (__DEV__) {
              console.log('[RealtimePoseService] Backpressure: slowing down frame transmission');
            }
            return;
          }
          if (parsed.type === 'speed_up') {
            this.isSlowed = false;
            if (__DEV__) {
              console.log('[RealtimePoseService] Backpressure: resuming normal frame transmission');
            }
            return;
          }

          // ── All other messages forwarded to the UI callback ———————————
          const message = parsed as import('@/interfaces/interfaces').JabRealtimeServerMessage;

          if (message.error) {
            callbacks.onError(new Error(message.error));
            return;
          }

          callbacks.onPoseUpdate(message);
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
        this.isSlowed = false;
      };
    } catch (error) {
      if (__DEV__) {
        console.error('[RealtimePoseService] Failed to create WebSocket', error);
      }
      callbacks.onStatusChange('error');
      callbacks.onError(error as Error);
    }
  }

  /**
   * Send a landmark frame to the backend.
   *
   * Validates that exactly 33 landmarks are present.
   * Drops the frame (returns `false`) when:
   *  - The WebSocket is not in OPEN state.
   *  - There are already {@link MAX_PENDING_FRAMES} unacknowledged frames
   *    (backpressure protection).
   *
   * C-01: Does NOT send any image data — only coordinate arrays.
   *
   * @param landmarks  - 33 normalised pose landmarks.
   * @param frameIndex - Monotonic frame counter for the session.
   * @param userId     - Optional authenticated user id.
   * @param sessionId  - Optional session id echoed from the backend.
   * @returns `true` if the payload was queued, `false` if the frame was dropped.
   */
  sendLandmarks(
    landmarks: LandmarkPoint[],
    frameIndex: number,
    userId?: string,
    sessionId?: string,
  ): boolean {
    if (landmarks.length !== 33) {
      if (__DEV__) {
        console.warn(
          `[RealtimePoseService] Expected 33 landmarks, got ${landmarks.length}. Frame dropped.`,
        );
      }
      return false;
    }

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (__DEV__) {
        console.warn('[RealtimePoseService] WebSocket not ready, dropping frame');
      }
      return false;
    }

    if (this.pendingFrames >= this.MAX_PENDING_FRAMES) {
      if (__DEV__) {
        console.warn('[RealtimePoseService] Backend overloaded, dropping frame');
      }
      return false;
    }

    if (this.isSlowed) {
      if (__DEV__) {
        console.warn('[RealtimePoseService] Backpressure active (slow_down), dropping frame');
      }
      return false;
    }

    try {
      const payload: LandmarkPayload = {
        landmarks,
        fps: 30,
        frame_index: frameIndex,
        ...(userId !== undefined && { user_id: userId }),
        ...(sessionId !== undefined && { session_id: sessionId }),
      };

      this.ws.send(JSON.stringify(payload));
      this.pendingFrames++;
      return true;
    } catch (error) {
      if (__DEV__) {
        console.error('[RealtimePoseService] Error sending landmarks', error);
      }
      this.callbacks?.onError(error as Error);
      return false;
    }
  }

  /** Close the WebSocket and reset all internal state. */
  disconnect(): void {
    this.isProcessing = false;
    this.isSlowed = false;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.callbacks = null;
    this.pendingFrames = 0;
  }

  /** Returns `true` when the WebSocket is in the OPEN state. */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /** Returns `true` while a session is actively processing frames. */
  getIsProcessing(): boolean {
    return this.isProcessing;
  }

  /** Number of frames sent but not yet acknowledged by the backend. */
  getPendingFrames(): number {
    return this.pendingFrames;
  }

  /**
   * Send a reset command to the backend, clearing its pose state machine.
   * Does nothing if the WebSocket is not open.
   */
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

/** Singleton instance used across the app. */
export const realtimePoseService = new RealtimePoseService();
