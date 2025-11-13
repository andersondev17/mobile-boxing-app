import { icons } from '@/constants/icons';
import type { CVPipelineLandmarks, CVPipelineResponse } from '@/interfaces/interfaces';
import { resetCounter } from '@/services/cvPipelineService';
import {
  realtimePoseService,
  type ConnectionStatus,
} from '@/services/realtimePoseService';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Line, Text as SvgText } from 'react-native-svg';

const FPS = 2; // 2 frames por segundo (500ms entre frames) - más estable para captura
const FRAME_INTERVAL = 1000 / FPS;

export default function RealtimeCounter() {
  const router = useRouter();
  const cameraRef = useRef<CameraView>(null);
  const frameIntervalRef = useRef<number | null>(null);
  const isCapturingRef = useRef(false); // Prevenir capturas concurrentes
  const [permission, requestPermission] = useCameraPermissions();

  // Estado de conexión
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [count, setCount] = useState(0);
  const [state, setState] = useState('Esperando');
  const [landmarks, setLandmarks] = useState<CVPipelineLandmarks | null>(null);

  // Estado de cámara
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [facing, setFacing] = useState<'front' | 'back'>('front');

  // Solicitar permisos al montar
  useEffect(() => {
    if (permission === null) {
      requestPermission();
    }
  }, [permission]);

  /**
   * Maneja actualizaciones de pose desde el WebSocket
   */
  const handlePoseUpdate = useCallback((data: CVPipelineResponse) => {
    setCount(data.count);
    setState(data.state);
    if (data.landmarks) {
      setLandmarks(data.landmarks);
    }
  }, []);

  /**
   * Maneja errores de WebSocket
   */
  const handleError = useCallback((error: Error) => {
    Alert.alert('Error de Conexión', error.message);
  }, []);

  /**
   * Captura y envía un frame al servidor
   */
  const captureAndSendFrame = useCallback(async () => {
    if (isCapturingRef.current || !cameraRef.current || !realtimePoseService.isConnected()) {
      return;
    }

    isCapturingRef.current = true;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.3,
        base64: true,
        skipProcessing: true,
      });

      if (photo?.base64) {
        const base64Image = `data:image/jpeg;base64,${photo.base64}`;
        realtimePoseService.sendFrame(base64Image);
      }
    } catch (error: any) {
      // Silenciar errores esperados de camera unmount
      if (!error?.message?.includes('unmounted')) {
        console.error('Error capturing frame:', error);
      }
    } finally {
      isCapturingRef.current = false;
    }
  }, []);

  /**
   * Inicia la captura de frames
   */
  const startFrameCapture = useCallback(() => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
    }

    frameIntervalRef.current = setInterval(captureAndSendFrame, FRAME_INTERVAL);
  }, [captureAndSendFrame]);

  /**
   * Detiene la captura de frames
   */
  const stopFrameCapture = useCallback(() => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, []);

  /**
   * Conecta al servidor WebSocket
   */
  const handleConnect = useCallback(() => {
    if (!isCameraReady) {
      Alert.alert('Cámara no lista', 'Espera a que la cámara esté activa');
      return;
    }

    realtimePoseService.connect({
      onStatusChange: setStatus,
      onPoseUpdate: handlePoseUpdate,
      onError: handleError,
    });

    startFrameCapture();
  }, [isCameraReady, handlePoseUpdate, handleError, startFrameCapture]);

  /**
   * Desconecta del servidor
   */
  const handleDisconnect = useCallback(() => {
    stopFrameCapture();
    realtimePoseService.disconnect();
    setLandmarks(null);
    setCount(0);
    setState('Esperando');
  }, [stopFrameCapture]);

  /**
   * Reinicia el contador
   */
  const handleReset = useCallback(async () => {
    try {
      await resetCounter();
      setCount(0);
      setState('Esperando');
      setLandmarks(null);
    } catch (error) {
      console.error('Error resetting counter:', error);
      Alert.alert('Error', 'No se pudo reiniciar el contador');
    }
  }, []);

  /**
   * Alterna la cámara
   */
  const toggleCamera = useCallback(() => {
    setFacing((current) => (current === 'front' ? 'back' : 'front'));
  }, []);

  /**
   * Cleanup al desmontar
   */
  useEffect(() => {
    return () => {
      handleDisconnect();
    };
  }, [handleDisconnect]);

  // Verificar permisos
  if (!permission || !permission.granted) {
    return (
      <SafeAreaView className="flex-1 bg-gymshock-dark-900 justify-center items-center">
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text className="text-white/60 font-spacemono text-sm mt-4">
          Solicitando permisos de cámara...
        </Text>
      </SafeAreaView>
    );
  }

  return (
    <View className="flex-1 bg-gymshock-dark-900">
      {/* Cámara */}
      <View className="flex-1 bg-black relative">
        <CameraView
          ref={cameraRef}
          style={{ flex: 1 }}
          facing={facing}
          onCameraReady={() => setIsCameraReady(true)}
        />

        {/* Overlay SVG para landmarks */}
        {landmarks && (
          <Svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
            }}
            viewBox="0 0 640 480"
            preserveAspectRatio="xMidYMid slice"
          >
            {/* Brazo derecho */}
            <Line
              x1={landmarks.right_shoulder[0]}
              y1={landmarks.right_shoulder[1]}
              x2={landmarks.right_elbow[0]}
              y2={landmarks.right_elbow[1]}
              stroke="#00FFFF"
              strokeWidth="3"
            />
            <Line
              x1={landmarks.right_elbow[0]}
              y1={landmarks.right_elbow[1]}
              x2={landmarks.right_wrist[0]}
              y2={landmarks.right_wrist[1]}
              stroke="#00FFFF"
              strokeWidth="3"
            />

            {/* Brazo izquierdo */}
            <Line
              x1={landmarks.left_shoulder[0]}
              y1={landmarks.left_shoulder[1]}
              x2={landmarks.left_elbow[0]}
              y2={landmarks.left_elbow[1]}
              stroke="#00FFFF"
              strokeWidth="3"
            />
            <Line
              x1={landmarks.left_elbow[0]}
              y1={landmarks.left_elbow[1]}
              x2={landmarks.left_wrist[0]}
              y2={landmarks.left_wrist[1]}
              stroke="#00FFFF"
              strokeWidth="3"
            />

            {/* Puntos - Hombros */}
            <Circle
              cx={landmarks.right_shoulder[0]}
              cy={landmarks.right_shoulder[1]}
              r="8"
              fill="#00FFFF"
            />
            <Circle
              cx={landmarks.left_shoulder[0]}
              cy={landmarks.left_shoulder[1]}
              r="8"
              fill="#00FFFF"
            />

            {/* Puntos - Codos */}
            <Circle cx={landmarks.right_elbow[0]} cy={landmarks.right_elbow[1]} r="8" fill="#FF00FF" />
            <Circle cx={landmarks.left_elbow[0]} cy={landmarks.left_elbow[1]} r="8" fill="#FF00FF" />

            {/* Puntos - Muñecas */}
            <Circle cx={landmarks.right_wrist[0]} cy={landmarks.right_wrist[1]} r="8" fill="#FFFF00" />
            <Circle cx={landmarks.left_wrist[0]} cy={landmarks.left_wrist[1]} r="8" fill="#FFFF00" />

            {/* Ángulos */}
            <SvgText
              x={landmarks.right_elbow[0] + 20}
              y={landmarks.right_elbow[1] - 20}
              fill="white"
              fontSize="20"
              fontWeight="bold"
            >
              {Math.round(landmarks.angle_r)}°
            </SvgText>
            <SvgText
              x={landmarks.left_elbow[0] + 20}
              y={landmarks.left_elbow[1] - 20}
              fill="white"
              fontSize="20"
              fontWeight="bold"
            >
              {Math.round(landmarks.angle_l)}°
            </SvgText>
          </Svg>
        )}

        {/* Controles superpuestos */}
        <SafeAreaView
          className="absolute top-0 left-0 right-0 bottom-0"
          style={{ pointerEvents: 'box-none' }}
        >
          {/* Header */}
          <View className="px-5 pt-4 flex-row justify-between items-center">
            <TouchableOpacity
              onPress={() => router.back()}
              className="w-10 h-10 rounded-full bg-black/50 items-center justify-center"
              style={{ pointerEvents: 'auto' }}
            >
              <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
            </TouchableOpacity>

            <TouchableOpacity
              onPress={toggleCamera}
              className="w-10 h-10 rounded-full bg-black/50 items-center justify-center"
              style={{ pointerEvents: 'auto' }}
            >
              <Text className="text-white text-xl">🔄</Text>
            </TouchableOpacity>
          </View>

          {/* Status Banner */}
          <View className="px-5 pt-4">
            <View
              className={`py-3 px-4 rounded-lg ${
                status === 'connected'
                  ? 'bg-green-500/90'
                  : status === 'connecting'
                    ? 'bg-yellow-500/90'
                    : status === 'error'
                      ? 'bg-red-500/90'
                      : 'bg-gray-500/90'
              }`}
              style={{ pointerEvents: 'none' }}
            >
              <Text className="text-white font-oswaldmed text-center">
                {status === 'connected'
                  ? '🟢 Conectado - Procesando...'
                  : status === 'connecting'
                    ? '🟡 Conectando...'
                    : status === 'error'
                      ? '🔴 Error de conexión'
                      : '🔴 Desconectado'}
              </Text>
            </View>
          </View>

          {/* Stats Display */}
          <View className="absolute bottom-32 left-0 right-0 px-6">
            <View
              className="bg-black/70 rounded-2xl p-6 items-center"
              style={{ pointerEvents: 'none' }}
            >
              <Text className="text-white/60 font-spacemono text-sm mb-2">CONTADOR</Text>
              <Text className="text-primary-500 font-oswaldbold text-6xl">{count}</Text>
              <Text className="text-white font-oswaldmed text-xl mt-2">{state}</Text>
            </View>
          </View>

          {/* Control Buttons */}
          <View className="absolute bottom-6 left-0 right-0 px-6">
            <View className="flex-row gap-3" style={{ pointerEvents: 'auto' }}>
              {status === 'connected' ? (
                <>
                  <TouchableOpacity
                    onPress={handleReset}
                    className="flex-1 bg-yellow-500 py-4 rounded-xl"
                  >
                    <Text className="text-white font-oswaldmed text-center text-lg">Reiniciar</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={handleDisconnect}
                    className="flex-1 bg-red-500 py-4 rounded-xl"
                  >
                    <Text className="text-white font-oswaldmed text-center text-lg">Detener</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <TouchableOpacity
                  onPress={handleConnect}
                  className="flex-1 bg-primary-500 py-4 rounded-xl"
                  disabled={!isCameraReady}
                >
                  <Text className="text-white font-oswaldmed text-center text-lg">
                    {isCameraReady ? 'Iniciar Análisis' : 'Iniciando cámara...'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </SafeAreaView>
      </View>
    </View>
  );
}
