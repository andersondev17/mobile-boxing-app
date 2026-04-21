/**
 * Schema alignment status vs backend (apps/backend/app/routes/boxing.py)
 *
 * ALIGNED:
 *   - JabRealtimeServerMessage.feedback        ← backend sends "feedback": string | null
 *   - JabRealtimeServerMessage.jab_detected    ← backend sends "jab_detected": bool
 *   - JabRealtimeServerMessage.frame_index     ← backend sends "frame_index": int | null
 *   - JabRealtimeServerMessage.tracking_state  ← backend sends "tracking_state": string
 *   - JabRealtimeServerMessage.session_id      ← backend echoes session identifier
 *   - CVPipelineLandmarks (named key format)   ← backend echoes landmark dict under "landmarks"
 *   - CVPipelineResponse.count / .state        ← used by realtime UI state machine
 *   - LandmarkPoint                            ← {x, y, z} normalised coordinate (MediaPipe)
 *
 * SEND payload format (mobile → backend):
 *   { landmarks: LandmarkPoint[], fps: 30, frame_index: number, user_id?, session_id? }
 *   See LandmarkPayload in realtimePoseService.ts.
 *   C-01: Never send base64 frames.
 */

export interface Exercise {
  _id: string;
  title: string;
  category: string;
  posterpath: string;
  difficulty: string;
  duration: string;
  description: string;
  technique: string;
  muscles: string[];
  equipment: string;
}

/**
 * A single normalised MediaPipe pose landmark.
 * Values are in the range [0, 1] relative to the frame dimensions.
 */
export interface LandmarkPoint {
  x: number;
  y: number;
  z: number;
}

/**
 * Named landmark keys returned by the backend CV pipeline for arm tracking.
 * Pixel coordinates within a 640×480 canvas.
 */
export interface CVPipelineLandmarks {
  right_shoulder: [number, number];
  right_elbow: [number, number];
  right_wrist: [number, number];
  left_shoulder: [number, number];
  left_elbow: [number, number];
  left_wrist: [number, number];
  angle_r: number;
  angle_l: number;
}

/** Response from the backend CV pipeline used to drive the realtime UI. */
export interface CVPipelineResponse {
  count: number;
  state: 'Esperando' | 'Sube' | 'Bien hecho' | 'Reinicio';
  landmarks?: CVPipelineLandmarks;
}

export interface ProcessVideoResult {
  videoUri: string;
  framesAnalyzed: number;
  baselineUsed: boolean;
  sessionId?: string;
  feedbackSummary: string[];
  metricsPath?: string;
  sessionFile?: string;
  sessionRows?: number;
  // New fields from updated pipeline
  punchTypeDetected?: string;
  baselineType?: string;
  baselineUsedPath?: string;
  avgScore?: number;
  minScore?: number;
  maxScore?: number;
  techniqueLevel?: string;
  coachingFeedback?: string[];
  motivationalMessages?: string[];
  processingMs?: number;
}

/**
 * Message sent from the backend WebSocket after processing a landmark frame.
 *
 * @property feedback       - Human-readable coaching feedback, or null.
 * @property jab_detected   - Whether a jab was detected in this frame.
 * @property frame_index    - Zero-based index of the processed frame, or null.
 * @property tracking_state - Pose-tracker lifecycle state.
 * @property session_id     - Backend session identifier (echoed back).
 * @property error          - Non-empty string when the backend returns an error.
 */
export interface JabRealtimeServerMessage {
  feedback: string | null;
  jab_detected: boolean;
  frame_index: number | null;
  tracking_state: 'searching' | 'tracking' | 'idle' | 'locked';
  session_id?: string;
  error?: string;
}

/**
 * @deprecated Use {@link JabRealtimeServerMessage} directly.
 * Kept for backward-compatibility with code that still references the old name.
 */
export type JabRealtimeFramePayload = JabRealtimeServerMessage;
