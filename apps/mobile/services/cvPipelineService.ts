import * as FileSystem from 'expo-file-system';
import type { ProcessVideoResult } from '@/interfaces/interfaces';

const getApiUrl = (): string => {
  const env = process.env.EXPO_PUBLIC_ENV || 'development';

  if (env === 'development') {
    const ip = process.env.EXPO_PUBLIC_LOCAL_IP || '192.168.1.26';
    const port = process.env.EXPO_PUBLIC_BACKEND_PORT || '8000';
    return `http://${ip}:${port}`;
  }

  return process.env.EXPO_PUBLIC_API_URL || '';
};

const API_BASE_URL = getApiUrl();

export async function uploadVideoForProcessing(videoUri: string): Promise<ProcessVideoResult> {
  console.log('📤 Uploading video:', videoUri);

  const formData = new FormData();
  formData.append('file', {
    uri: videoUri,
    type: 'video/mp4',
    name: 'exercise.mp4',
  } as any);

  const response = await fetch(`${API_BASE_URL}/video/process_video`, {
    method: 'POST',
    body: formData,
  });

  console.log('📥 Response status:', response.status);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ Error response:', errorText);
    throw new Error(`Error ${response.status}: ${errorText}`);
  }

  const pullupsHeader = response.headers.get('X-Total-Pullups') || response.headers.get('x-total-pullups');
  console.log('📊 Pullups header value:', pullupsHeader);
  const totalPullups = parseInt(pullupsHeader || '0');
  console.log('✅ Total pullups:', totalPullups);

  const arrayBuffer = await response.arrayBuffer();
  console.log('📦 Received arrayBuffer size:', arrayBuffer.byteLength, 'bytes');

  const uint8Array = new Uint8Array(arrayBuffer);

  let binary = '';
  const chunkSize = 8192;
  for (let i = 0; i < uint8Array.length; i += chunkSize) {
    const chunk = uint8Array.subarray(i, Math.min(i + chunkSize, uint8Array.length));
    binary += String.fromCharCode.apply(null, Array.from(chunk));
  }

  console.log('🔄 Converting to base64...');
  const base64 = btoa(binary);
  console.log('✅ Base64 length:', base64.length);

  const outputUri = `${FileSystem.cacheDirectory}processed_${Date.now()}.mp4`;
  console.log('💾 Writing to:', outputUri);

  await FileSystem.writeAsStringAsync(outputUri, base64, { encoding: FileSystem.EncodingType.Base64 });

  console.log('✅ Video saved successfully');

  return {
    videoUri: outputUri,
    totalPullups,
  };
}

export async function resetCounter(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/video/reset_counter`);
    if (!response.ok) {
      throw new Error('Error al reiniciar contador');
    }
  } catch (error) {
    console.error('Error resetting counter:', error);
    throw error;
  }
}
