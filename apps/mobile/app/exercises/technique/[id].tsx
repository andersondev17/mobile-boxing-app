import { icons } from '@/constants/icons';
import { uploadVideoForProcessing } from '@/services/cvPipelineService';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { ResizeMode, Video } from 'expo-av';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function TechniqueCapture() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [facing, setFacing] = useState<'front' | 'back'>('front');

  useEffect(() => {
    if (permission === null) {
      requestPermission();
    }
  }, [permission]);

  const toggleCameraFacing = () => {
    setFacing(current => current === 'front' ? 'back' : 'front');
  };

  if (!permission || !permission.granted) {
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
    if (!cameraRef.current) return;

    if (isRecording) {
      cameraRef.current.stopRecording();
      setIsRecording(false);
    } else {
      setIsRecording(true);
      const video = await cameraRef.current.recordAsync({ maxDuration: 60 });
      if (video) {
        setVideoUri(video.uri);
      }
    }
  };

  const handleProcessVideo = async () => {
    if (!videoUri) return;

    setIsProcessing(true);
    try {
      const result = await uploadVideoForProcessing(videoUri);
      router.replace({
        pathname: '/exercises/technique/results',
        params: {
          videoUri: result.videoUri,
          totalPullups: result.totalPullups,
          exerciseId: id,
        },
      });
    } catch (error) {
      Alert.alert('Error', 'No se pudo procesar el video. Intenta de nuevo.');
      setIsProcessing(false);
    }
  };

  const handleRetake = () => {
    setVideoUri(null);
    setIsRecording(false);
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
                  Procesando video...
                </Text>
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
      <CameraView ref={cameraRef} style={{ flex: 1 }} mode="video" facing={facing} />

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
            className={`w-20 h-20 rounded-full border-4 border-white items-center justify-center ${
              isRecording ? 'bg-red-500' : 'bg-transparent'
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
