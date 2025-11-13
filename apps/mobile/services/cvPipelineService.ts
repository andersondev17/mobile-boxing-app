import type { ProcessVideoResult } from '@/interfaces/interfaces';
import { API_BASE_URL } from '@/lib/api/client';
import * as FileSystem from 'expo-file-system/legacy';

export async function uploadVideoForProcessing(videoUri: string): Promise<ProcessVideoResult> {
    console.log('📤 Uploading video');

  const fileInfo = await FileSystem.getInfoAsync(videoUri);
  if (!fileInfo.exists) {
    throw new Error('El archivo de video no existe');
  }

  const uploadResult = await FileSystem.uploadAsync(
    `${API_BASE_URL}/video/process_video`,
    videoUri,
    {
      httpMethod: 'POST',
      uploadType: FileSystem.FileSystemUploadType.MULTIPART,
      fieldName: 'file',
    }
  );

  if (uploadResult.status !== 200) {
    throw new Error(`Error del servidor: ${uploadResult.status}`);
  }

  if (!uploadResult.body) {
    throw new Error('El servidor no devolvió respuesta');
  }

  const response = JSON.parse(uploadResult.body);
  const { video_base64, total_pullups } = response;

  if (!video_base64) {
    throw new Error('El servidor no devolvió el video procesado');
  }

  const outputUri = `${FileSystem.cacheDirectory}processed_${Date.now()}.mp4`;

  await FileSystem.writeAsStringAsync(
    outputUri,
    video_base64,
    { encoding: FileSystem.EncodingType.Base64 }
  );

  const savedFileInfo = await FileSystem.getInfoAsync(outputUri);
  if (!savedFileInfo.exists) {
    throw new Error('El archivo guardado no existe');
  }

  return {
    videoUri: outputUri,
    totalPullups: total_pullups,
  };
}

export async function resetCounter(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/video/reset_counter`);

  if (!response.ok) {
    throw new Error('Error al reiniciar contador');
  }
}
