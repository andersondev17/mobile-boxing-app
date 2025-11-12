import { icons } from '@/constants/icons';
import type { CVPipelineLandmarks, CVPipelineResponse } from '@/interfaces/interfaces';
import { resetCounter } from '@/services/cvPipelineService';
import {
  realtimePoseService,
  type ConnectionStatus,
} from '@/services/realtimePoseService';
import * as FileSystem from 'expo-file-system/legacy';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Line, Text as SvgText } from 'react-native-svg';
import {
  Camera,
  useCameraDevices,
  useCameraFormat,
  useCameraPermission
} from 'react-native-vision-camera';

// Configuración optimizada para detección en tiempo real
const TARGET_FPS = 10; // 10 FPS - balance óptimo performance/latency
const TARGET_WIDTH = 640; // Resolución suficiente para MediaPipe
const TARGET_HEIGHT = 480;
const JPEG_QUALITY = 0.75; // Balance calidad/tamaño

export default function RealtimeVisionCounter() {
  const router = useRouter();
  const devices = useCameraDevices();

  // Usar la primera cámara disponible por defecto
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  // Auto-seleccionar primera cámara disponible
  useEffect(() => {
    if (devices.length > 0 && !selectedDeviceId) {
      setSelectedDeviceId(devices[0].id);
      if (__DEV__) {
        console.log('📸 Auto-selected device:', devices[0]);
      }
    }
  }, [devices, selectedDeviceId]);

  const device = devices.find(d => d.id === selectedDeviceId) ?? null;
  const { hasPermission, requestPermission } = useCameraPermission();

  const format = useCameraFormat(device ?? undefined, [
    { videoResolution: { width: TARGET_WIDTH, height: TARGET_HEIGHT } },
    { fps: TARGET_FPS },
  ]);

  // Debug cameras
  useEffect(() => {
    if (__DEV__) {
      console.log('📸 All devices:', devices);
      console.log('📸 Current device:', device);
    }
  }, [devices, device]);

  // Estado de conexión
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [count, setCount] = useState(0);
  const [state, setState] = useState('Esperando');
  const [landmarks, setLandmarks] = useState<CVPipelineLandmarks | null>(null);

  // Estado de cámara
  const [isActive, setIsActive] = useState(false);

  // Solicitar permisos al montar
  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

  /**
   * Maneja actualizaciones de pose desde el WebSocket
   */
  const handlePoseUpdate = useCallback((data: CVPipelineResponse) => {
    if (__DEV__) {
      console.log('📥 Pose update:', { count: data.count, state: data.state, hasLandmarks: !!data.landmarks });
    }
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
   * Referencia a la cámara para capturas
   */
  const cameraRef = useRef<Camera>(null);
  const intervalRef = useRef<number | null>(null);
  const isCapturingRef = useRef(false);

  /**
   * Captura frame usando takePhoto + FileSystem para base64
   */
  const captureAndSendFrame = useCallback(async () => {
    if (!cameraRef.current || isCapturingRef.current || !realtimePoseService.isConnected()) {
      return;
    }

    isCapturingRef.current = true;

    try {
      const photo = await cameraRef.current.takePhoto({
        flash: 'off',
      });

      const base64 = await FileSystem.readAsStringAsync(`file://${photo.path}`, {
        encoding: 'base64',
      });

      const sent = realtimePoseService.sendFrame(`data:image/jpeg;base64,${base64}`);
      if (__DEV__ && sent) {
        console.log('📸 Frame sent:', base64.length, 'bytes');
      }
    } catch (error) {
      if (__DEV__) {
        console.error('❌ Frame capture error:', error);
      }
    } finally {
      isCapturingRef.current = false;
    }
  }, []);

  /**
   * Conecta al servidor WebSocket e inicia captura de frames
   */
  const handleConnect = useCallback(() => {
    realtimePoseService.connect({
      onStatusChange: setStatus,
      onPoseUpdate: handlePoseUpdate,
      onError: handleError,
    });

    setIsActive(true);

    // Iniciar intervalo de captura (10 FPS = 100ms)
    intervalRef.current = setInterval(() => {
      captureAndSendFrame();
    }, 1000 / TARGET_FPS);
  }, [handlePoseUpdate, handleError, captureAndSendFrame]);

  /**
   * Desconecta del servidor y detiene captura
   */
  const handleDisconnect = useCallback(() => {
    setIsActive(false);

    // Detener intervalo de captura
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    realtimePoseService.disconnect();
    setLandmarks(null);
    setCount(0);
    setState('Esperando');
  }, []);

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
      if (__DEV__) {
        console.error('❌ Error resetting counter:', error);
      }
      Alert.alert('Error', 'No se pudo reiniciar el contador');
    }
  }, []);

  /**
   * Cambia entre cámaras disponibles
   */
  const toggleCameraFacing = useCallback(() => {
    if (devices.length <= 1) return;

    const currentIndex = devices.findIndex(d => d.id === selectedDeviceId);
    const nextIndex = (currentIndex + 1) % devices.length;
    setSelectedDeviceId(devices[nextIndex].id);
  }, [devices, selectedDeviceId]);

  /**
   * Cleanup al desmontar
   */
  useEffect(() => {
    return () => {
      handleDisconnect();
    };
  }, [handleDisconnect]);

  // Verificar permisos
  if (!hasPermission) {
    return (
      <SafeAreaView className="flex-1 bg-gymshock-dark-900 justify-center items-center">
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text className="text-white/60 font-spacemono text-sm mt-4">
          Solicitando permisos de cámara...
        </Text>
      </SafeAreaView>
    );
  }

  // Verificar dispositivo
  if (!device) {
    return (
      <SafeAreaView className="flex-1 bg-gymshock-dark-900 justify-center items-center px-6">
        <Text className="text-white font-oswaldbold text-xl mb-4 text-center">
          Cámara no disponible
        </Text>
        <Text className="text-white/60 font-spacemono text-sm mb-6 text-center">
          {devices.length === 0
            ? 'No se detectaron cámaras en el dispositivo'
            : 'Error inicializando la cámara'}
        </Text>
        <Text className="text-white/40 font-spacemono text-xs mb-8 text-center">
          Tip: En emulador Android, configura la cámara en AVD Manager
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="bg-primary-500 px-6 py-3 rounded-xl"
        >
          <Text className="text-white font-oswaldmed">Volver</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <View className="flex-1 bg-gymshock-dark-900">
      {/* Cámara con captura por takePhoto */}
      <View className="flex-1 bg-black relative">
        <Camera
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          device={device}
          isActive={isActive}
          format={format}
          fps={TARGET_FPS}
          photo={true}
          enableZoomGesture={true}
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
            viewBox={`0 0 ${TARGET_WIDTH} ${TARGET_HEIGHT}`}
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
              onPress={toggleCameraFacing}
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
                  ? `🟢 Conectado - ${TARGET_FPS} FPS`
                  : status === 'connecting'
                    ? '🟡 Conectando...'
                    : status === 'error'
                      ? '🔴 Error de conexión'
                      : '🔴 Desconectado'}
              </Text>
            </View>
          </View>

          {/* Stats Display - Compacto */}
          <View className="absolute bottom-24 left-0 right-0 px-6">
            <View
              className="bg-black/70 rounded-xl p-3 items-center"
              style={{ pointerEvents: 'none' }}
            >
              <Text className="text-white/60 font-spacemono text-xs mb-1">CONTADOR</Text>
              <Text className="text-primary-500 font-oswaldbold text-4xl">{count}</Text>
              <Text className="text-white font-oswaldmed text-base mt-1">{state}</Text>
            </View>
          </View>

          {/* Control Buttons */}
          <View className="absolute bottom-6 left-0 right-0 px-6">
            <View className="flex-row gap-3" style={{ pointerEvents: 'auto' }}>
              {status === 'connected' ? (
                <>
                  <TouchableOpacity
                    onPress={handleReset}
                    className="flex-1 bg-yellow-500 py-3 rounded-xl"
                  >
                    <Text className="text-white font-oswaldmed text-center">Reiniciar</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={handleDisconnect}
                    className="flex-1 bg-red-500 py-3 rounded-xl"
                  >
                    <Text className="text-white font-oswaldmed text-center">Detener</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <TouchableOpacity
                  onPress={handleConnect}
                  className="flex-1 bg-primary-500 py-3 rounded-xl"
                >
                  <Text className="text-white font-oswaldmed text-center">
                    Iniciar (10 FPS)
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
