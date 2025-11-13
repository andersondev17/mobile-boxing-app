import { icons } from '@/constants/icons';
import { ResizeMode, Video } from 'expo-av';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { Alert, Share, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as MediaLibrary from 'expo-media-library';

export default function TechniqueResults() {
  const router = useRouter();
  const { videoUri, totalPullups, exerciseId } = useLocalSearchParams();
  const videoRef = useRef<Video>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleSaveToGallery = async () => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permisos requeridos', 'Necesitamos permiso para guardar el video');
        return;
      }

      await MediaLibrary.saveToLibraryAsync(videoUri as string);
      Alert.alert('Éxito', 'Video guardado en tu galería');
    } catch (error) {
      Alert.alert('Error', 'No se pudo guardar el video');
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `¡Completé ${totalPullups} dominadas con análisis de IA!`,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleRetry = () => {
    router.replace({
      pathname: '/exercises/technique/[id]',
      params: { id: exerciseId },
    });
  };

  return (
    <SafeAreaView className="flex-1 bg-gymshock-dark-900">
      <View className="flex-1">
        <View className="px-5 pt-4 pb-3 flex-row justify-between items-center">
          <TouchableOpacity onPress={() => router.back()} className="w-10 h-10 items-center justify-center">
            <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
          </TouchableOpacity>
          <Text className="text-white font-oswaldbold text-xl">Resultados</Text>
          <View className="w-10" />
        </View>

        <View className="px-5 mb-6">
          <View className="bg-primary-500/20 border border-primary-400/40 rounded-2xl p-6 items-center">
            <Text className="text-primary-200 font-oswaldmed text-sm uppercase tracking-wider mb-2">
              Total de Repeticiones
            </Text>
            <Text className="text-white font-oswaldbold text-6xl">
              {totalPullups}
            </Text>
          </View>
        </View>

        <View className="flex-1 px-5">
          <View className="bg-gymshock-dark-800/50 rounded-2xl overflow-hidden" style={{ aspectRatio: 16 / 9 }}>
            <Video
              ref={videoRef}
              source={{ uri: videoUri as string }}
              style={{ width: '100%', height: '100%' }}
              resizeMode={ResizeMode.CONTAIN}
              isLooping
              shouldPlay={isPlaying}
              onPlaybackStatusUpdate={(status) => {
                if ('isPlaying' in status) {
                  setIsPlaying(status.isPlaying);
                }
              }}
              useNativeControls
            />
          </View>

          <Text className="text-white/60 font-spacemono text-xs text-center mt-4">
            Video procesado con análisis de técnica en tiempo real
          </Text>
        </View>

        <View className="px-5 pb-6 space-y-3">
          <TouchableOpacity
            onPress={handleSaveToGallery}
            className="bg-primary-500 py-4 rounded-xl flex-row items-center justify-center"
          >
            <Text className="text-white font-oswaldmed text-lg">Guardar en Galería</Text>
          </TouchableOpacity>

          <View className="flex-row gap-3">
            <TouchableOpacity
              onPress={handleShare}
              className="flex-1 bg-white/10 py-4 rounded-xl"
            >
              <Text className="text-white font-oswaldmed text-center">Compartir</Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleRetry}
              className="flex-1 bg-white/10 py-4 rounded-xl"
            >
              <Text className="text-white font-oswaldmed text-center">Reintentar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}
