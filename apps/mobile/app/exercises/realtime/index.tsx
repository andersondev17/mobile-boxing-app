/**
 * RealtimeCounter
 *
 * Real-time jab counter powered by the WebSocket pose service.
 *
 * Sprint 2 changes:
 *  - Consent gate (C-05): biometric consent is checked and requested before
 *    the camera is ever activated.
 *  - Landmark-only pipeline: captures frames via CameraView, converts them to
 *    33-point landmark arrays via TFLite (placeholder hook), and sends only
 *    the coordinates — no base64 — to the backend (C-01).
 *  - Callback fix: service now uses `onPoseUpdate` (was `onFrame`).
 *
 * @module app/exercises/realtime
 */

import BiometricConsentModal from '@/components/BiometricConsentModal';
import { icons } from '@/constants/icons';
import type { CVPipelineLandmarks, JabRealtimeServerMessage, LandmarkPoint } from '@/interfaces/interfaces';
import { post, get } from '@/lib/api/client';
import { useAuthStore } from '@/store/authStore';
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

/** Target send rate — matches the backend expectation. */
const FPS = 30;
const FRAME_INTERVAL = 1000 / FPS;

/**
 * Shape of the consent-check endpoint response.
 * GET /consent/{userId}/check?consent_type=biometric_data
 */
interface ConsentCheckResponse {
  has_consent: boolean;
}

/**
 * Real-time jab counter screen.
 *
 * Consent gate prevents the camera from activating until the user has
 * granted biometric consent (Ley 1581). On first visit the
 * {@link BiometricConsentModal} is shown; on subsequent visits the
 * stored consent record is verified via the backend.
 */
export default function RealtimeCounter() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const cameraRef = useRef<CameraView>(null);
  const frameIndexRef = useRef(0);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [permission, requestPermission] = useCameraPermissions();

  // Consent gate state
  const [consentGranted, setConsentGranted] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [consentLoading, setConsentLoading] = useState(true);

  // WebSocket / session state
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [count, setCount] = useState(0);
  const [state, setState] = useState('Esperando');
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [landmarks, setLandmarks] = useState<CVPipelineLandmarks | null>(null);

  // Camera state
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [facing, setFacing] = useState<'front' | 'back'>('front');

  // -----------------------------------------------------------------------
  // Consent gate: check stored consent on mount
  // -----------------------------------------------------------------------

  useEffect(() => {
    let cancelled = false;

    const checkConsent = async (): Promise<void> => {
      if (!user?.id) {
        // Not logged in — show modal, let the modal POST record consent
        if (!cancelled) {
          setConsentLoading(false);
          setShowConsentModal(true);
        }
        return;
      }

      try {
        const result = await get<ConsentCheckResponse>(
          `/consent/${user.id}/check?consent_type=biometric_data`,
        );
        if (!cancelled) {
          if (result.has_consent) {
            setConsentGranted(true);
          } else {
            setShowConsentModal(true);
          }
        }
      } catch {
        // Endpoint not reachable (e.g. offline) — show modal to be safe
        if (!cancelled) {
          setShowConsentModal(true);
        }
      } finally {
        if (!cancelled) {
          setConsentLoading(false);
        }
      }
    };

    void checkConsent();
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  /**
   * Called when the user taps "Permitir análisis" in the consent modal.
   * Records consent on the backend and activates the camera gate.
   */
  const handleConsentAccept = useCallback(async (): Promise<void> => {
    try {
      await post('/consent/', {
        consent_type: 'biometric_data',
        granted: true,
      });
    } catch {
      // Non-fatal: store locally as granted even if the POST fails.
      // The modal has already presented the legal information.
    }
    setShowConsentModal(false);
    setConsentGranted(true);
  }, []);

  /**
   * Called when the user taps "Ahora no" in the consent modal.
   */
  const handleConsentDecline = useCallback((): void => {
    setShowConsentModal(false);
    router.back();
  }, [router]);

  // -----------------------------------------------------------------------
  // Camera permissions
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (permission === null) {
      void requestPermission();
    }
  }, [permission]);

  // -----------------------------------------------------------------------
  // WebSocket callbacks
  // -----------------------------------------------------------------------

  /**
   * Receives processed server messages and updates UI state.
   */
  const handlePoseUpdate = useCallback((data: JabRealtimeServerMessage) => {
    if (typeof data.jab_detected === 'boolean' && data.jab_detected) {
      setCount((prev) => prev + 1);
    }
    if (data.tracking_state) {
      const stateMap: Record<string, string> = {
        searching: 'Buscando cuerpo...',
        tracking: 'Analizando técnica',
        locked: 'Analizando técnica',
        idle: 'Listo',
      };
      setState(stateMap[data.tracking_state] ?? 'Esperando');
    }
    if (data.session_id) {
      setSessionId(data.session_id);
    }
    if (data.feedback) {
      // Feedback is shown in the UI status bar — no separate state needed
    }
  }, []);

  /**
   * Surfaces WebSocket errors as alerts.
   */
  const handleError = useCallback((error: Error) => {
    Alert.alert('Error de Conexión', error.message);
  }, []);

  // -----------------------------------------------------------------------
  // Landmark extraction + send pipeline
  // -----------------------------------------------------------------------

  /**
   * Placeholder: extracts 33 MediaPipe-format landmarks from the camera frame.
   *
   * In production this will be replaced by a TFLite frame-processor worklet.
   * The returned array always has exactly 33 elements so `sendLandmarks` can
   * validate it.
   *
   * @returns 33 zero-filled landmark points (stub).
   */
  const extractLandmarksFromFrame = useCallback((): LandmarkPoint[] => {
    // TODO Sprint 3: replace with actual TFLite frame-processor output.
    // The processor runs on the JS worklet thread via react-native-vision-camera.
    return Array.from({ length: 33 }, () => ({ x: 0, y: 0, z: 0 }));
  }, []);

  /**
   * Extracts landmarks and forwards them to the WebSocket service.
   * Drops the frame silently if the connection is not ready.
   */
  const captureAndSendLandmarks = useCallback((): void => {
    if (!realtimePoseService.isConnected()) {
      return;
    }

    const landmarkArray = extractLandmarksFromFrame();
    const currentIndex = frameIndexRef.current;
    frameIndexRef.current += 1;

    realtimePoseService.sendLandmarks(
      landmarkArray,
      currentIndex,
      user?.id,
      sessionId,
    );
  }, [extractLandmarksFromFrame, user?.id, sessionId]);

  // -----------------------------------------------------------------------
  // Frame interval management
  // -----------------------------------------------------------------------

  /**
   * Starts the periodic landmark-send loop.
   */
  const startFrameCapture = useCallback((): void => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
    }
    frameIndexRef.current = 0;
    frameIntervalRef.current = setInterval(captureAndSendLandmarks, FRAME_INTERVAL);
  }, [captureAndSendLandmarks]);

  /**
   * Stops the periodic landmark-send loop.
   */
  const stopFrameCapture = useCallback((): void => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, []);

  // -----------------------------------------------------------------------
  // Session controls
  // -----------------------------------------------------------------------

  /**
   * Opens the WebSocket connection and starts sending landmarks.
   * Requires both camera readiness and granted consent.
   */
  const handleConnect = useCallback((): void => {
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
   * Closes the WebSocket connection and resets session state.
   */
  const handleDisconnect = useCallback((): void => {
    stopFrameCapture();
    realtimePoseService.disconnect();
    setLandmarks(null);
    setCount(0);
    setState('Esperando');
    setSessionId(undefined);
  }, [stopFrameCapture]);

  /**
   * Sends a reset command to the backend state machine and clears local UI state.
   */
  const handleReset = useCallback((): void => {
    realtimePoseService.requestReset();
    setCount(0);
    setState('Esperando');
    setLandmarks(null);
  }, []);

  /** Toggles front/back camera. */
  const toggleCamera = useCallback((): void => {
    setFacing((current) => (current === 'front' ? 'back' : 'front'));
  }, []);

  /** Cleanup on unmount. */
  useEffect(() => {
    return () => {
      handleDisconnect();
    };
  }, [handleDisconnect]);

  // -----------------------------------------------------------------------
  // Render guards
  // -----------------------------------------------------------------------

  if (consentLoading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#0D0D0D', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text style={{ color: 'rgba(255,255,255,0.6)', marginTop: 12, fontSize: 13 }}>
          Verificando permisos...
        </Text>
      </SafeAreaView>
    );
  }

  if (!permission || !permission.granted) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: '#0D0D0D', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text style={{ color: 'rgba(255,255,255,0.6)', marginTop: 12, fontSize: 13 }}>
          Solicitando permisos de cámara...
        </Text>
      </SafeAreaView>
    );
  }

  // -----------------------------------------------------------------------
  // Main render
  // -----------------------------------------------------------------------

  return (
    <View className="flex-1 bg-gymshock-dark-900">
      {/* Biometric consent modal — blocks camera until resolved */}
      <BiometricConsentModal
        visible={showConsentModal}
        onAccept={handleConsentAccept}
        onDecline={handleConsentDecline}
      />

      {/* Camera — only rendered after consent is granted */}
      {consentGranted && (
        <View className="flex-1 bg-black relative">
          <CameraView
            ref={cameraRef}
            style={{ flex: 1 }}
            facing={facing}
            onCameraReady={() => setIsCameraReady(true)}
          />

          {/* SVG overlay for arm landmarks */}
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
              {/* Right arm */}
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

              {/* Left arm */}
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

              {/* Shoulder points */}
              <Circle cx={landmarks.right_shoulder[0]} cy={landmarks.right_shoulder[1]} r="8" fill="#00FFFF" />
              <Circle cx={landmarks.left_shoulder[0]} cy={landmarks.left_shoulder[1]} r="8" fill="#00FFFF" />

              {/* Elbow points */}
              <Circle cx={landmarks.right_elbow[0]} cy={landmarks.right_elbow[1]} r="8" fill="#FF00FF" />
              <Circle cx={landmarks.left_elbow[0]} cy={landmarks.left_elbow[1]} r="8" fill="#FF00FF" />

              {/* Wrist points */}
              <Circle cx={landmarks.right_wrist[0]} cy={landmarks.right_wrist[1]} r="8" fill="#FFFF00" />
              <Circle cx={landmarks.left_wrist[0]} cy={landmarks.left_wrist[1]} r="8" fill="#FFFF00" />

              {/* Angles */}
              <SvgText x={landmarks.right_elbow[0] + 20} y={landmarks.right_elbow[1] - 20} fill="white" fontSize="20" fontWeight="bold">
                {Math.round(landmarks.angle_r)}
              </SvgText>
              <SvgText x={landmarks.left_elbow[0] + 20} y={landmarks.left_elbow[1] - 20} fill="white" fontSize="20" fontWeight="bold">
                {Math.round(landmarks.angle_l)}
              </SvgText>
            </Svg>
          )}

          {/* Overlaid controls */}
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
                    ? 'Conectado - Procesando...'
                    : status === 'connecting'
                      ? 'Conectando...'
                      : status === 'error'
                        ? 'Error de conexión'
                        : 'Desconectado'}
                </Text>
              </View>
            </View>

            {/* Stats */}
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

            {/* Control buttons */}
            <View className="absolute bottom-6 left-0 right-0 px-6">
              <View className="flex-row gap-3" style={{ pointerEvents: 'auto' }}>
                {status === 'connected' ? (
                  <>
                    <TouchableOpacity onPress={handleReset} className="flex-1 bg-yellow-500 py-4 rounded-xl">
                      <Text className="text-white font-oswaldmed text-center text-lg">Reiniciar</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={handleDisconnect} className="flex-1 bg-red-500 py-4 rounded-xl">
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
      )}
    </View>
  );
}
