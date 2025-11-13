import type { ProcessVideoResult } from '@/interfaces/interfaces';
import { uploadVideoForProcessing } from '@/services/cvPipelineService';
import { useCallback, useState } from 'react';

/**
 * Hook para procesar videos grabados
 *
 * Web flow:
 * 1. Seleccionar archivo
 * 2. Validar tipo y tamaño
 * 3. Subir a /video/process_video
 * 4. Recibir video procesado + header X-Total-Pullups
 * 5. Mostrar resultado
 */
export function useVideoProcessing() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const processVideo = useCallback(async (videoUri: string): Promise<ProcessVideoResult | null> => {
    setIsProcessing(true);
    setProgress(0);
    setError(null);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      const result = await uploadVideoForProcessing(videoUri);

      setProgress(100);
      clearInterval(progressInterval);

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al procesar el video';
      setError(errorMessage);
      clearInterval(progressInterval);
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsProcessing(false);
    setProgress(0);
    setError(null);
  }, []);

  return {
    isProcessing,
    progress,
    error,
    processVideo,
    reset,
  };
}
