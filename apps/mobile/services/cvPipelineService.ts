// apps/mobile/services/cvPipelineService.ts
import type { ProcessVideoResult } from '@/interfaces/interfaces';
import { API_BASE_URL } from '@/lib/api/client';
import * as FileSystem from 'expo-file-system/legacy';

export async function uploadVideoForProcessing(
  videoUri: string,
  sessionId?: string
): Promise<ProcessVideoResult> {
  console.log('📤 Uploading video');

  const fileInfo = await FileSystem.getInfoAsync(videoUri);
  if (!fileInfo.exists) {
    throw new Error('El archivo de video no existe');
  }

  // Construir URL con session_id si está presente
  let uploadUrl = `${API_BASE_URL}/boxing/videos/upload`;
  if (sessionId) {
    uploadUrl += `?session_id=${encodeURIComponent(sessionId)}`;
  }

  console.log('🔗 URL de upload:', uploadUrl);

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

  // PARSEAR LA RESPUESTA JSON
  const response = JSON.parse(uploadResult.body);
  const {
    video_base64,
    frames_analyzed,
    baseline_used,
    session_id,
    feedback_summary,
    metrics_path,
    session_file,
    session_rows
  } = response;

  if (!video_base64) {
    throw new Error('El servidor no devolvió el video procesado');
  }

  const outputUri = `${FileSystem.cacheDirectory}processed_${Date.now()}.mp4`;

  await FileSystem.writeAsStringAsync(
    outputUri,
    video_base64,
    { encoding: FileSystem.EncodingType.Base64 }
  );

  // Verificar que el archivo se guardó correctamente
  const savedFileInfo = await FileSystem.getInfoAsync(outputUri);
  if (!savedFileInfo.exists) {
    throw new Error('Error al guardar el video procesado');
  }

  return {
    videoUri: outputUri,
    framesAnalyzed: frames_analyzed || 0,
    baselineUsed: baseline_used || false,
    sessionId: session_id,
    feedbackSummary: feedback_summary || [],
    metricsPath: metrics_path,
    sessionFile: session_file,
    sessionRows: session_rows,
  };
}