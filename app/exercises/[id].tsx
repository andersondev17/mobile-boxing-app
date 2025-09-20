import { icons } from "@/constants/icons";
import { fetchExerciseById } from "@/services/exerciseService";
import useFetch from "@/services/usefetch";
import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useCallback, useMemo } from 'react';
import { ActivityIndicator, Image, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from "react-native-safe-area-context";

const StatsCard = React.memo(({ label, value, size = "lg" }: { label: string; value: string; size?: "lg" | "sm" }) => (
  <View className="flex-1 bg-gymshock-dark-800/50 backdrop-blur-sm p-4 rounded-2xl border border-white/5">
    <Text className="text-primary-400 font-oswaldmed text-xs uppercase tracking-wider mb-1">
      {label}
    </Text>
    <Text className={`text-white font-oswaldbold ${size === "lg" ? "text-lg" : "text-sm"} capitalize`}>
      {value}
    </Text>
  </View>
));
StatsCard.displayName = "StatsCard";


const MuscleTag = React.memo(({ muscle }: { muscle: string }) => (
  <View className="bg-primary-500/15 backdrop-blur-sm px-5 py-3 rounded-full border border-primary-500/30">
    <Text className="text-primary-300 font-oswaldmed text-sm">
      {muscle}
    </Text>
  </View>
));
MuscleTag.displayName = "MuscleTag";


const ExerciseDetails = () => {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const { data: exercise, loading, error } = useFetch(() => fetchExerciseById(id as string));

  // Memoized handlers
  const handleBack = useCallback(() => router.back(), [router]);
  const handleSave = useCallback(() => {
    // TODO: Implement save functionality
    console.log('Save exercise:', exercise?.title);
  }, [exercise?.title]);
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
      <SafeAreaView className="bg-black flex-1 justify-center items-center">
        <ActivityIndicator size="large" color="#FF6B35" />
        <Text className="text-white/60 mt-4 font-oswald">Loading workout...</Text>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView className="bg-black flex-1 justify-center items-center px-6">
        <Text className="text-white font-oswaldbold text-xl mb-4 text-center">
          Error al cargar ejercicio
        </Text>
        <TouchableOpacity
          onPress={handleBack}
          className="bg-primary-500 px-6 py-3 rounded-xl"
        >
          <Text className="text-white font-oswaldmed">Volver</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <View className="bg-black flex-1">


      <ScrollView
        contentContainerStyle={{ paddingBottom: 140 }}
        showsVerticalScrollIndicator={false}
        bounces={false}
        scrollEventThrottle={16}
        removeClippedSubviews={true}
      >
        {/* Hero Section */}
        <View className="relative">
          <Image
            source={{
              uri: exercise?.posterpath || 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png'
            }}
            className="w-full h-[60vh]"
            resizeMode="cover"
            onError={() => console.log('Image load error')}
          />

          {/* Header Controls */}
          <View className="absolute top-16 left-0 right-0 flex-row justify-between items-center px-6">
            <TouchableOpacity
              onPress={handleBack}
              className="w-11 h-11 rounded-full bg-black/60 backdrop-blur-sm items-center justify-center"
              activeOpacity={0.8}
              accessibilityRole="button"
            >
              <Image source={icons.arrow} className="w-5 h-5 rotate-180" tintColor="#fff" />
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleSave}
              className="w-11 h-11 rounded-full bg-black/60 backdrop-blur-sm items-center justify-center"
              activeOpacity={0.8}
            >
              <Image source={icons.save} className="w-5 h-5" tintColor="#fff" />
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            onPress={handleAITechnique}
            className="absolute bottom-16 right-6"
            activeOpacity={0.9}
          >
            <View className="bg-accent-neon rounded-2xl px-6 py-4 flex-row items-center shadow-2xl">
              <Image source={icons.play} className="w-5 h-5 mr-3" tintColor="#fff" />
              <Text className="text-white font-oswaldbold text-sm">TÉCNICA IA</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Content Container */}
        <View className="px-6 -mt-8 relative z-10">
          <View className="bg-black/95 backdrop-blur-xl rounded-3xl p-6 border border-white/10">

            <View className="bg-primary-500 self-start px-4 py-2 rounded-full mb-6">
              <Text className="text-white font-oswaldbold text-xs uppercase tracking-widest">
                {categoryDisplay}
              </Text>
            </View>

            <Text className="text-white font-oswaldbold text-4xl leading-tight mb-8">
              {exercise?.title}
            </Text>

            <View className="flex-row gap-4 mb-10">
              <StatsCard label="Nivel" value={exercise?.difficulty || 'N/A'} />
              <StatsCard label="Duración" value={exercise?.duration || 'N/A'} />
              <StatsCard label="Equipo" value={equipmentDisplay} size="sm" />
            </View>

            {/* Target Muscles */}
            {exercise?.muscles && exercise.muscles.length > 0 && (
              <View className="mb-10">
                <Text className="text-white font-oswaldbold text-xl mb-6">
                  MÚSCULOS OBJETIVO
                </Text>
                <View className="flex-row flex-wrap gap-3">
                  {exercise?.muscles.map((muscle, index) => (
                    <MuscleTag key={`${muscle}-${index}`} muscle={muscle} />
                  ))}
                </View>
              </View>
            )}

            <View className="mb-8">
              <Text className="text-white font-oswaldbold text-xl mb-4">
                DESCRIPCIÓN
              </Text>
              <Text className="text-white/90 font-oswald text-base leading-7">
                {exercise?.description || "Descripción no disponible"}
              </Text>
            </View>

            <View className="mb-6">
              <Text className="text-white font-oswaldbold text-xl mb-4">
                TÉCNICA CORRECTA
              </Text>
              <Text className="text-white/90 font-oswald text-base leading-7">
                {exercise?.technique || "Técnica no disponible"}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>

      <View className="absolute bottom-0 left-0 right-0">
        <View className="bg-gradient-to-t from-black via-black/95 to-transparent pt-8 pb-10 px-6">
          <TouchableOpacity
            onPress={handleBack}
            className="w-full bg-primary-500 py-5 rounded-2xl items-center justify-center shadow-2xl"
            activeOpacity={0.9}
          >
            <Text className="text-white font-oswaldbold text-lg">
              Volver
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  )
}

export default ExerciseDetails