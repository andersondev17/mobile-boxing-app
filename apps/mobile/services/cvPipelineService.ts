// apps/mobile/services/cvPipelineService.ts
import type { ProcessVideoResult } from '@/interfaces/interfaces';
import { API_BASE_URL } from '@/lib/api/client';
import * as FileSystem from 'expo-file-system/legacy';

/**
 * Uploads a locally-recorded video to the backend for CV processing.
 *
 * C-01 compliance: the backend returns a `video_url` streaming path — no
 * base64 bytes are received or written to the device filesystem. The caller
 * should stream the processed video directly from the returned URL.
 *
 * Backend response shape for POST /boxing/videos/upload:
 *   { video_url, frames_analyzed, baseline_used, session_id,
 *     feedback_summary, session_rows }
 *
 * @param videoUri   - Local `file://` URI of the video to upload.
 * @param sessionId  - Optional existing session to associate with.
 * @returns ProcessVideoResult with `videoUri` set to the backend streaming URL.
 */
export async function uploadVideoForProcessing(
  videoUri: string,
  sessionId?: string
): Promise<ProcessVideoResult> {
  console.log('Uploading video for processing');

  const fileInfo = await FileSystem.getInfoAsync(videoUri);
  if (!fileInfo.exists) {
    throw new Error('El archivo de video no existe');
  }

  // Build upload URL, appending optional session_id query param.
  let uploadUrl = `${API_BASE_URL}/boxing/videos/upload`;
  if (sessionId) {
    uploadUrl += `?session_id=${encodeURIComponent(sessionId)}`;
  }

  const uploadResult = await FileSystem.uploadAsync(
    uploadUrl,
    videoUri,
    {
      httpMethod: 'POST',
      uploadType: FileSystem.FileSystemUploadType.MULTIPART,
      fieldName: 'file',
    }
  );

  if (uploadResult.status !== 200) {
    throw new Error(`Error del servidor: ${uploadResult.status} - ${uploadResult.body}`);
  }

  if (!uploadResult.body) {
    throw new Error('El servidor no devolvió respuesta');
  }

  // Parse the backend response — only metadata and a streaming URL are expected.
  // C-01: never read or write video/image bytes on the device.
  const response = JSON.parse(uploadResult.body) as {
    video_url: string;
    frames_analyzed?: number;
    baseline_used?: boolean;
    session_id?: string;
    feedback_summary?: string[];
    session_rows?: number;
    punch_type_detected?: string;
    baseline_type?: string;
    baseline_used_path?: string;
    avg_score?: number;
    min_score?: number;
    max_score?: number;
    technique_level?: string;
    coaching_feedback?: string[];
    motivational_messages?: string[];
    processing_ms?: number;
  };

  if (!response.video_url) {
    throw new Error('El servidor no devolvió la URL del video procesado');
  }

  // Return the backend streaming URL directly — no local file is written.
  return {
    videoUri: `${API_BASE_URL}${response.video_url}`,
    framesAnalyzed: response.frames_analyzed ?? 0,
    baselineUsed: response.baseline_used ?? false,
    sessionId: response.session_id,
    feedbackSummary: response.feedback_summary ?? [],
    sessionRows: response.session_rows,
    punchTypeDetected: response.punch_type_detected,
    baselineType: response.baseline_type,
    baselineUsedPath: response.baseline_used_path,
    avgScore: response.avg_score ?? 0,
    minScore: response.min_score ?? 0,
    maxScore: response.max_score ?? 0,
    techniqueLevel: response.technique_level,
    coachingFeedback: response.coaching_feedback ?? [],
    motivationalMessages: response.motivational_messages ?? [],
    processingMs: response.processing_ms,
  };
}