import CustomButton from '@/components/CustomButton';
import { icons } from '@/constants/icons';
import { ResizeMode, Video } from 'expo-av';
import { Image } from 'expo-image';
import * as MediaLibrary from 'expo-media-library';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useMemo, useRef, useState } from 'react';
import { Alert, ScrollView, Share, Text, TouchableOpacity, View } from 'react-native';

/**
 * - Metrics row (speed, extension, score)
 * - Group feedback into categories (critical / improve / good)
 * - Small highlights thumbnails (uses uploaded file as placeholder)
 *
 */


// Example placeholder thumbnail (user uploaded). Use this path as URL in your env.
const SAMPLE_THUMBNAIL = '/mnt/data/57aed67a-37ae-4e3c-a110-47d2c480f4fd.png';

/**
 * Group feedback lines into 3 categories using tiny heuristics.
 * This is intentionally simple so the logic is easy to replace by backend scores later.
 */
const groupFeedback = (lines: string[]) => {
  const critical: string[] = [];
  const improve: string[] = [];
  const good: string[] = [];

  for (const raw of lines) {
    const s = raw.toLowerCase();

    if (s.includes('baja') || s.includes('coloca mal') || s.includes('expuesto') || s.includes('muy abierto')) {
      critical.push(raw);
    } else if (s.includes('falta') || s.includes('mejorar') || s.includes('rotación') || s.includes('extiende')) {
      improve.push(raw);
    } else {
      good.push(raw);
    }
  }

  return { critical, improve, good };
};

/**
 * Simple heuristic score for a jab.
 * INPUT: framesAnalyzed, counts of feedback categories.
 * OUTPUT: 0..100 integer.
 *
 * This is not clinical — it's a UX-friendly score to motivate users.
 * Replace formula with real metrics when available.
 */
const computeJabScore = (frames: number, counts: { critical: number; improve: number; good: number }) => {
  // base from frames (more frames -> slightly better precision)
  const base = Math.min(40, Math.round(Math.log(Math.max(1, frames)) * 10)); // 0..40
  // penalty for criticals
  const penalty = counts.critical * 10;
  // small bonus for goods
  const bonus = counts.good * 6;
  let score = base + bonus - penalty + 40; // center around 40-80
  score = Math.max(0, Math.min(100, score));
  return score;
};

const parseSummary = (summaryParam: string | string[] | undefined): string[] => {
  if (!summaryParam) return [];
  const raw = Array.isArray(summaryParam) ? summaryParam[0] : summaryParam;
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export default function TechniqueResults() {
  const router = useRouter();
  const params = useLocalSearchParams();

  const videoUri = (params.videoUri as string) ?? '';
  const framesAnalyzed = Number(params.framesAnalyzed ?? 0);
  const baselineUsed = (params.baselineUsed ?? '') === 'true';
  const feedbackSummary = useMemo(
    () => parseSummary(params.feedbackSummary),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [params.feedbackSummary]
  );

  const exerciseId = (params.exerciseId as string) ?? '';
  const sessionId = params.sessionId as string | undefined;

  const videoRef = useRef<Video>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Group feedback now (very small and readable)
  const grouped = useMemo(() => groupFeedback(feedbackSummary), [feedbackSummary]);

  // Compute a jab score with a tiny heuristic
  const jabScore = useMemo(
    () =>
      computeJabScore(framesAnalyzed, {
        critical: grouped.critical.length,
        improve: grouped.improve.length,
        good: grouped.good.length,
      }),
    [framesAnalyzed, grouped]
  );

  const handleSaveToGallery = async () => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permisos requeridos', 'Necesitamos permiso para guardar el video');
        return;
      }
      await MediaLibrary.saveToLibraryAsync(videoUri);
      Alert.alert('Éxito', 'Video guardado en tu galería');
    } catch {
      Alert.alert('Error', 'No se pudo guardar el video');
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Analicé ${framesAnalyzed} frames con la IA de técnica${baselineUsed ? ' usando baseline personalizado' : ''}.`,
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


  const Metric = ({ label, value }: { label: string; value: string | number }) => (
    <View className="flex-1 items-center">
      <Text className="text-white/60 font-spacemono text-xs uppercase">{label}</Text>
      <Text className="text-white font-oswaldbold text-2xl mt-1">{value}</Text>
    </View>
  );

  const CategoryCard = ({ title, items, tone }: { title: string; items: string[]; tone?: 'danger' | 'warn' | 'good' }) => {
    // minimal color coding using existing palette classes
    const headerClass =
      tone === 'danger' ? 'text-primary-300' : tone === 'warn' ? 'text-primary-200' : 'text-primary-100';
    return (
      <View className="rounded-2xl p-4 bg-white/5 border border-white/10 mb-3">
        <Text className={`font-oswaldbold ${headerClass} mb-2`}>{title}</Text>
        {items.length === 0 ? (
          <Text className="text-white/70 font-spacemono text-xs">— Ningún punto detectado</Text>
        ) : (
          items.map((it, idx) => (
            <Text key={`${it}-${idx}`} className="text-white/70 font-spacemono text-xs mb-1">
              • {it}
            </Text>
          ))
        )}
      </View>
    );
  };

  return (
    <ScrollView className="flex-1 bg-gymshock-dark-900">
      {/* Header  */}
      <View className="px-5 pt-4 pb-3 flex-row items-center justify-between bg-gymshock-dark-900/70 backdrop-blur-xl border-b border-white/5">
        <TouchableOpacity
          onPress={() => router.back()}
          className="w-10 h-10 rounded-full bg-white/5 items-center justify-center border border-white/10"
          activeOpacity={0.85}
        >
          <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
        </TouchableOpacity>
        <Text className="text-white font-oswaldbold text-xl">Resultados — Jab</Text>
        <View className="w-10" />
      </View>

      {/* Summary + metrics  */}
      <View className="px-5 mt-6">
        <View className="rounded-3xl px-6 py-5 bg-white/5 border border-white/10 backdrop-blur-xl">
          <Text className="text-primary-200 font-oswaldmed text-sm uppercase text-center tracking-wider mb-4">
            Resumen del análisis
          </Text>

          <View className="flex-row items-center mb-4">
            <Metric label="Detección con IA" value={baselineUsed ? 'Activo' : 'No'} />
            <Metric label="Score" value={`${jabScore}/100`} />
          </View>

          {/* progress bar representation */}
          <View className="h-3 rounded-full bg-white/10 overflow-hidden mt-2">
            <View
              style={{ width: `${jabScore}%` }}
              className="h-3 rounded-full bg-gradient-to-r from-[#C29B2E] to-[#F5D068]"
            />
          </View>
        </View>
      </View>

      {/* Video container*/}
      <View className="px-5 mt-6">
        <View className="rounded-3xl overflow-hidden bg-white/5 border border-white/10 backdrop-blur-xl" style={{ aspectRatio: 16 / 9 }}>
          <Video
            ref={videoRef}
            source={{ uri: videoUri }}
            style={{ width: '100%', height: '100%' }}
            resizeMode={ResizeMode.CONTAIN}
            shouldPlay={isPlaying}
            isLooping
            useNativeControls
            onPlaybackStatusUpdate={(status) => {
              if ('isPlaying' in status) setIsPlaying(status.isPlaying);
            }}
          />
        </View>
        <Text className="text-white/50 font-spacemono text-xs text-center mt-3">Video procesado con anotaciones del modelo de técnica</Text>
      </View>

      {/* Feedback grouped */}
      <View className="px-5 mt-6">
        <CategoryCard title="Crítico (arreglar primero)" items={grouped.critical} tone="danger" />
        <CategoryCard title="Para mejorar" items={grouped.improve} tone="warn" />
        <CategoryCard title="Bien ejecutado" items={grouped.good} tone="good" />
      </View>

      {/* Actions */}
      <View className="px-5 pb-10 mt-6 space-y-4">
        <CustomButton title="Guardar en galería" onPress={handleSaveToGallery} variant="primary" />

        <View className="flex-row gap-4">
          <TouchableOpacity
            onPress={handleShare}
            className="flex-1 py-4 rounded-2xl bg-white/5 border border-white/10 items-center justify-center backdrop-blur-lg"
          >
            <Text className="text-white font-oswaldmed text-base">Compartir</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleRetry}
            className="flex-1 py-4 rounded-2xl bg-white/5 border border-white/10 items-center justify-center backdrop-blur-lg"
          >
            <Text className="text-white font-oswaldmed text-base">Reintentar</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}
