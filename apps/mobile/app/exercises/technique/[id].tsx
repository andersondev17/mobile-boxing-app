import { icons } from '@/constants/icons';
import { useVideoProcessing } from '@/hooks/useVideoProcessing';
import { ResizeMode, Video } from 'expo-av';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Camera, useCameraDevice, useCameraDevices, useCameraPermission, VideoFile } from 'react-native-vision-camera';

export default function TechniqueCapture() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const cameraRef = useRef<Camera>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [facing, setFacing] = useState<'front' | 'back'>('front');
  const [cameraReady, setCameraReady] = useState(false);

  const devices = useCameraDevices(); // opcional: para enumerar dispositivos
  const device = useCameraDevice(facing); // usar 'front' o 'back'
  const { hasPermission: hasCameraPermission, requestPermission: requestCameraPermission } = useCameraPermission();

  const { isProcessing, progress, error, processVideo, reset } = useVideoProcessing();

  useEffect(() => {
    (async () => {
      // Si aún no tiene permiso, solicitarlo
      if (!hasCameraPermission) {
        await requestCameraPermission();
      }
    })();
  }, [hasCameraPermission, requestCameraPermission]);


  const toggleCameraFacing = () => {
    setFacing(current => current === 'front' ? 'back' : 'front');
  };

  if (!hasCameraPermission) {
    return (
      <SafeAreaView className="flex-1 bg-gymshock-dark-900 justify-center items-center">
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text className="text-white/60 font-spacemono text-sm mt-4">
          Solicitando permisos...
        </Text>
      </SafeAreaView>
    );
  }

  const handleRecord = async () => {
    if (!cameraRef.current || !device) return;

    try {
      if (isRecording) {
        // detiene la grabación -> llamará a onRecordingFinished
        await cameraRef.current.stopRecording();
        setIsRecording(false);
        return;
      }

      setIsRecording(true);

      cameraRef.current.startRecording({
        onRecordingFinished: (video: VideoFile) => {
          // video.path es la ruta local en Android/iOS
          const path = (video.path ?? (video as any).uri) as string;
          // asegura formato file://
          const uri = path.startsWith('file://') ? path : `file://${path}`;
          setVideoUri(uri);
          setIsRecording(false);
        },
        onRecordingError: (error: any) => {
          console.error('Recording error:', error);
          setIsRecording(false);
          Alert.alert('Error', 'Error al grabar el video. Intenta de nuevo.');
        },
      });
    } catch (err) {
      console.error(err);
      setIsRecording(false);
    }
  };


  const handleProcessVideo = async () => {
    if (!videoUri) return;

    const result = await processVideo(videoUri);

    if (result) {
      router.replace({
        pathname: '/exercises/technique/results',
        params: {
          videoUri: result.videoUri,
          totalPullups: result.totalPullups,
          exerciseId: id,
        },
      });
    } else {
      Alert.alert('Error', error || 'No se pudo procesar el video. Intenta de nuevo.');
    }
  };

  const handleRetake = () => {
    setVideoUri(null);
    setIsRecording(false);
    reset();
  };

  if (videoUri) {
    return (
      <SafeAreaView className="flex-1 bg-gymshock-dark-900">
        <View className="flex-1">
          <View className="px-5 pt-4 pb-3">
            <Text className="text-white font-oswaldbold text-xl text-center">
              Vista Previa
            </Text>
          </View>

          <View className="flex-1 bg-black">
            <Video
              source={{ uri: videoUri }}
              style={{ flex: 1 }}
              resizeMode={ResizeMode.CONTAIN}
              shouldPlay
              isLooping
              useNativeControls
            />
          </View>

          <View className="px-6 py-6">
            {isProcessing ? (
              <View className="items-center py-6">
                <ActivityIndicator size="large" color="#C29B2E" />
                <Text className="text-white/60 font-spacemono text-sm mt-4">
                  Procesando video... {progress}%
                </Text>
                {error && (
                  <Text className="text-red-500 font-spacemono text-xs mt-2">
                    {error}
                  </Text>
                )}
              </View>
            ) : (
              <View className="space-y-3">
                <TouchableOpacity
                  onPress={handleProcessVideo}
                  className="bg-primary-500 py-4 rounded-xl"
                >
                  <Text className="text-white font-oswaldmed text-center text-lg">
                    Analizar Técnica
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={handleRetake}
                  className="bg-white/10 py-4 rounded-xl"
                >
                  <Text className="text-white font-oswaldmed text-center text-lg">
                    Grabar de nuevo
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View className="flex-1 bg-black">
      {device == null ? (
        <View style={{ flex: 1, backgroundColor: 'black', justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#C29B2E" />
          <Text className="text-white/60 font-spacemono text-sm mt-4">Inicializando cámara...</Text>
        </View>
      ) : (
        <Camera
          ref={cameraRef}
          style={{ flex: 1 }}
          device={device}
          isActive={true}
          video={true}
          onInitialized={() => setCameraReady(true)}
        // videoBitRate="high"
        // fps={30} 
        />
      )}
      <SafeAreaView className="absolute top-0 left-0 right-0 bottom-0" style={{ pointerEvents: 'box-none' }}>
        <View className="absolute top-14 left-5">
          <TouchableOpacity
            onPress={() => router.back()}
            className="w-10 h-10 rounded-full bg-black/50 items-center justify-center"
            style={{ pointerEvents: 'auto' }}
          >
            <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
          </TouchableOpacity>
        </View>

        <View className="absolute top-14 right-5">
          <TouchableOpacity
            onPress={toggleCameraFacing}
            className="w-10 h-10 rounded-full bg-black/50 items-center justify-center"
            style={{ pointerEvents: 'auto' }}
          >
            <Text className="text-white text-xl">🔄</Text>
          </TouchableOpacity>
        </View>

        <View className="absolute bottom-10 left-0 right-0 items-center" style={{ pointerEvents: 'box-none' }}>
          {isRecording && (
            <View className="mb-4 bg-red-500 px-4 py-2 rounded-full">
              <Text className="text-white font-oswaldmed">Grabando...</Text>
            </View>
          )}

          <TouchableOpacity
            onPress={handleRecord}
            className={`w-20 h-20 rounded-full border-4 border-white items-center justify-center ${isRecording ? 'bg-red-500' : 'bg-transparent'
              }`}
            style={{ pointerEvents: 'auto' }}
          >
            <View className={`w-12 h-12 ${isRecording ? 'bg-white' : 'bg-red-500'} rounded-full`} />
          </TouchableOpacity>

          <Text className="text-white/60 font-spacemono text-xs mt-4">
            Máximo 60 segundos
          </Text>
        </View>
      </SafeAreaView>
    </View>
  );
}
