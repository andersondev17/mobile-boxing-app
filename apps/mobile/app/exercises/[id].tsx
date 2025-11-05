import CustomButton from "@/components/CustomButton";
import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import { fetchExerciseById } from "@/services/exerciseService";
import useFetch from "@/services/usefetch";
import { useActionSheet } from "@expo/react-native-action-sheet";
import { Image } from "expo-image";
import { LinearGradient } from 'expo-linear-gradient';
import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useCallback, useMemo } from 'react';
import { ActivityIndicator, Dimensions, ScrollView, Share, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from "react-native-safe-area-context";

const { height: SCREEN_HEIGHT } = Dimensions.get('window');
const HERO_HEIGHT = SCREEN_HEIGHT * 0.92;

const StatsCard = React.memo(({ label, value, size = "lg" }: { label: string; value: string; size?: "lg" | "sm" }) => (
  <View className="flex-1 bg-gymshock-dark-800/10 backdrop-blur-md p-3.5 rounded-xl border border-white/20">
    <Text className="text-primary-300 font-oswaldmed text-[10px] uppercase tracking-wider mb-0.5" numberOfLines={1}>
      {label}
    </Text>
    <Text className={`text-white font-spacemono ${size === "lg" ? "text-sm" : "text-xs"} capitalize font-semibold`}>
      {value}
    </Text>
  </View>
));
StatsCard.displayName = "StatsCard";


const MuscleTag = React.memo(({ muscle }: { muscle: string }) => (
  <View className="bg-primary-500/20 px-4 py-2 rounded-full border border-primary-400/40">
    <Text className="text-primary-200 font-spacemono text-xs">
      {muscle}
    </Text>
  </View>
));
MuscleTag.displayName = "MuscleTag";


const ExerciseDetails = () => {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const { data: exercise, loading, error } = useFetch(() => fetchExerciseById(id as string));
  const { showActionSheetWithOptions } = useActionSheet();

  const handleShare = useCallback(() => {
    if (!exercise) return;

    showActionSheetWithOptions({
      options: ['Compartir Ejercicio', 'Cancelar'],
      cancelButtonIndex: 1,
      title: exercise.title,
      tintColor: '#C29B2E',
      containerStyle: { backgroundColor: '#1a1a1f' },
      textStyle: { color: '#ffffff', fontFamily: 'Oswald-Medium' },
    }, async (buttonIndex) => {
      if (buttonIndex === 0) {
        try {
          await Share.share({
            message: `${exercise.title} - ¡Mira este ejercicio!`,
            url: `exercises://exercises/${exercise._id}`,
          });
        } catch (err) {
          console.error('Error compartiendo ejercicio:', err);
        }
      }
    });
  }, [exercise, showActionSheetWithOptions]);

  // Memoized handlers
  const handleBack = useCallback(() => router.back(), [router]);
  const handleAITechnique = useCallback(() => {
    // TODO: Navigate to AI technique 
    console.log('AI Technique for:', exercise?.title);
  }, [exercise?.title]);

  // Memoized computations
  const categoryDisplay = useMemo(() =>
    exercise?.category?.replace('_', ' ') || 'Sin categoría',
    [exercise?.category]
  );

  const equipmentDisplay = useMemo(() =>
    exercise?.equipment || 'Ninguno',
    [exercise?.equipment]
  );

  if (loading) {
    return (
      <SafeAreaView className="bg-gymshock-dark-900 flex-1 justify-center items-center">
        <ActivityIndicator size="large" color="#C29B2E" />
        <Text className="text-white/60 mt-4 font-oswald">Cargando...</Text>
      </SafeAreaView>
    );
  }

  if (error || !exercise) {
    return (
      <SafeAreaView className="bg-gymshock-dark-900 flex-1 justify-center items-center px-6">
        <Text className="text-white font-oswaldbold text-xl mb-4 text-center">
          Error al cargar ejercicio
        </Text>
        <TouchableOpacity
          onPress={handleBack}
          className="bg-primary-500 px-6 py-3 rounded-xl"
          activeOpacity={0.8}
        >
          <Text className="text-white font-oswaldmed">Volver</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <View className="bg-gymshock-dark-900 flex-1">


      <ScrollView
        showsVerticalScrollIndicator={false}
        bounces={false}
        scrollEventThrottle={16}
      >
        {/* Hero Section */}
        <View style={{ height: HERO_HEIGHT }} className="relative">
          <Image
            source={{ uri: exercise.posterpath }}
            style={{ width: '100%', height: '100%' }}
            contentFit="cover"
            transition={300}
          />

          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.4)', 'rgba(0,0,0,0.95)']}
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
          />

          {/* Header Controls */}
          <View className="absolute top-14 left-0 right-0 flex-row justify-between items-center px-5">
            <TouchableOpacity
              onPress={handleBack}
              className="w-10 h-10 rounded-full  backdrop-blur-md items-center justify-center"
              activeOpacity={0.7}
            >
              <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleShare}
              className="w-10 h-10 rounded-full backdrop-blur-md items-center justify-center"
              activeOpacity={0.7}
            >
              <Image source={icons.share} style={{ width: 18, height: 18 }} tintColor="#fff" />
            </TouchableOpacity>
          </View>

          <View className="absolute bottom-0 left-0 right-0 px-6 pb-20">
            <View className="mb-5">
              <Text className="text-white font-oswaldbold text-4xl mb-2">
                {exercise.title}
              </Text>
              <Text className="text-white/70 font-spacemono text-xs uppercase tracking-widest">
                {categoryDisplay}
              </Text>
            </View>
            <View className="flex-row gap-3 mb-5">
              <StatsCard label="Nivel" value={exercise.difficulty || 'N/A'} />
              <StatsCard label="Duración" value={exercise.duration || 'N/A'} />
              <StatsCard label="Equipo" value={equipmentDisplay} size="sm" />
            </View>

            <CustomButton
              title="Aprender Técnica con IA"
              rightIcon={<Image source={icons.play} style={{ width: 20, height: 20 }} tintColor="#fff" />}
              onPress={handleAITechnique}
              variant="primary"
            />
          </View>
        </View>

        {/* Content Section  */}
        <View className=" px-5 pb-20">
          <Image
            source={images.bg}
            className="absolute w-full h-full opacity-25 bg-backgroundImage-premiumGradient"
          />
          <View className="rounded-3xl overflow-hidden mb-5 -mt-12" style={{ shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.5, shadowRadius: 16, elevation: 12 }}>
            {/* Background Image */}
            <View style={{ height: 200 }} className="relative">
              <Image
                source={{ uri: exercise.posterpath }}
                style={{ width: '100%', height: '100%' }}
                contentFit="cover"
                autoplay={false}
              />
              <LinearGradient
                colors={['transparent', 'rgba(17,17,17,0.8)', '#111111']}
                style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
              />
            </View>

            {/* Card Content */}
            <View className="bg-gymshock-dark-800/95  px-6 pb-6">
              <Text className="text-white font-oswaldbold text-2xl mb-2 -mt-2">
                Sobre este ejercicio
              </Text>
              <Text className="text-white/60 font-spacemono text-xs mb-4">
                {categoryDisplay} · {exercise.difficulty}
              </Text>
              <Text className="text-white/80 font-spacemono text-sm leading-6 mb-5">
                {exercise.description || "Descripción no disponible"}
              </Text>

              {/* Muscles Tags */}
              {exercise.muscles?.length > 0 && (
                <View className="flex-row flex-wrap gap-2">
                  {exercise.muscles.map((muscle, index) => (
                    <MuscleTag key={`${muscle}-${index}`} muscle={muscle} />
                  ))}
                </View>
              )}
            </View>
          </View>

          {/* Technique Card */}
          {exercise.technique && (
            <View className="bg-gymshock-dark-800/95  rounded-3xl p-6 mb-5 border border-white/5">
              <View className="flex-row items-center mb-4">
                <View className="w-10 h-10 rounded-full bg-primary-500/20 items-center justify-center mr-3">
                  <Text className="text-primary-400 text-xl">✓</Text>
                </View>
                <Text className="text-white font-oswaldbold text-xl flex-1">
                  Técnica Correcta
                </Text>
              </View>
              <Text className="text-white/80 font-spacemono text-sm leading-6">
                {exercise.technique}
              </Text>
            </View>
          )}

          {/* Additional Info Card */}
          <View className="bg-gymshock-dark-800/95  rounded-3xl p-6 border border-white/5">
            <Text className="text-white font-oswaldbold text-xl mb-4">
              Información Adicional
            </Text>
            <View className="space-y-3">
              <View className="flex-row justify-between items-center py-2 border-b border-white/5">
                <Text className="text-white/60 font-spacemono text-sm">Categoría</Text>
                <Text className="text-white font-spacemono text-sm capitalize">{categoryDisplay}</Text>
              </View>
              <View className="flex-row justify-between items-center py-2 border-b border-white/5">
                <Text className="text-white/60 font-spacemono text-sm">Nivel</Text>
                <Text className="text-white font-spacemono text-sm capitalize">{exercise.difficulty}</Text>
              </View>
              <View className="flex-row justify-between items-center py-2">
                <Text className="text-white/60 font-spacemono text-sm">Equipo</Text>
                <Text className="text-white font-spacemono text-sm capitalize">{equipmentDisplay}</Text>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

export default ExerciseDetails;