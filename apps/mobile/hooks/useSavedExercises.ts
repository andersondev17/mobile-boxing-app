// apps/mobile/hooks/useSavedExercises.ts
import { LocalVideoKey, localVideos } from '@/constants/videos';
import { Exercise } from '@/interfaces/interfaces';
import { useAuthStore } from '@/store/authStore';
import { useFocusEffect } from '@react-navigation/native';
import { useSQLiteContext } from 'expo-sqlite';
import { useCallback, useEffect, useState } from 'react';
import uuid from 'react-native-uuid';


// Helper para normalizar
const mapDbExerciseToExercise = (ex: any): Exercise => {
    const resolveImageUrl = (posterUrl: string): string => {
        if (posterUrl.startsWith('http')) {
            return posterUrl;
        }
        
        const localVideo = localVideos[posterUrl as LocalVideoKey];
        return typeof localVideo === 'object' ? localVideo.uri : posterUrl;
    };

    return {
        _id: ex.id,
        title: ex.title,
        posterpath: resolveImageUrl(ex.poster_url),
        category: ex.category,
        difficulty: ex.difficulty,
        duration: `${ex.duration_min} min`,
        description: ex.description,
        technique: ex.technique,
        muscles: Array.isArray(ex.muscles) ? ex.muscles : JSON.parse(ex.muscles || '[]'),
        equipment: ex.equipment || ''
    };
};

export function useSavedExercises() {
  const db = useSQLiteContext();
  const { isAuthenticated, user } = useAuthStore();
  const [savedExercises, setSavedExercises] = useState<Exercise[]>([]);
  const [savedIdsSet, setSavedIdsSet] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const userId = isAuthenticated && user?.email ? user.email : 'guest';

  const loadSavedIds = useCallback(async () => {
    if (!db) return new Set<string>();

    try {
      const result = await db.getAllAsync<{ exercise_id: string }>(
        `SELECT exercise_id FROM saved_exercises WHERE user_id = ?`,
        [userId]
      );
      return new Set(result.map(row => row.exercise_id));
    } catch (err) {
      console.error('Error loading saved IDs:', err);
      return new Set<string>();
    }
  }, [db, userId]);

  const fetchSaved = useCallback(async () => {
    if (!db) return;

    setLoading(true);
    try {
      const ids = await loadSavedIds();
      setSavedIdsSet(ids);

      if (ids.size > 0) {
        const placeholders = Array(ids.size).fill('?').join(',');
        const result = await db.getAllAsync<any>(
          `SELECT e.*, s.saved_at
           FROM saved_exercises s
           JOIN exercises e ON s.exercise_id = e.id
           WHERE s.user_id = ? AND s.exercise_id IN (${placeholders})
           ORDER BY s.saved_at DESC`,
          [userId, ...Array.from(ids)]
        );
        
        // ✅ FIX: Normalizar AQUÍ
        const normalized = result.map(mapDbExerciseToExercise);
        setSavedExercises(normalized);
      } else {
        setSavedExercises([]);
      }
    } catch (err) {
      console.error('Error fetching saved exercises:', err);
    } finally {
      setLoading(false);
    }
  }, [db, userId, loadSavedIds]);

  const toggleSave = useCallback(async (exerciseId: string, exerciseData?: Exercise) => {
    if (!db) return false;

    const isCurrentlySaved = savedIdsSet.has(exerciseId);

    if (isCurrentlySaved) {
      setSavedIdsSet(prev => {
        const newSet = new Set(prev);
        newSet.delete(exerciseId);
        return newSet;
      });
      setSavedExercises(prev => prev.filter(ex => ex._id !== exerciseId));
    } else if (exerciseData) {
      setSavedIdsSet(prev => new Set(prev).add(exerciseId));
      setSavedExercises(prev => [exerciseData, ...prev]);
    }

    try {
      if (isCurrentlySaved) {
        await db.runAsync(
          'DELETE FROM saved_exercises WHERE user_id = ? AND exercise_id = ?',
          [userId, exerciseId]
        );
        return false;
      }

      await db.runAsync(
        'INSERT OR REPLACE INTO saved_exercises (id, user_id, exercise_id) VALUES (?, ?, ?)',
        [uuid.v4() as string, userId, exerciseId]
      );
      return true;
    } catch (err) {
      console.error('Error toggling save:', err);
      const currentIds = await loadSavedIds();
      setSavedIdsSet(currentIds);
      await fetchSaved();
      return isCurrentlySaved;
    }
  }, [db, userId, savedIdsSet, loadSavedIds, fetchSaved]);

  useEffect(() => {
    fetchSaved();
  }, [fetchSaved]);

  useFocusEffect(
    useCallback(() => {
      fetchSaved();
    }, [fetchSaved])
  );

  const isExerciseSaved = useCallback((exerciseId: string) => {
    return savedIdsSet.has(exerciseId);
  }, [savedIdsSet]);

  return {
    savedExercises,
    loading,
    savedIds: savedIdsSet,
    isExerciseSaved,
    toggleSave,
    refresh: fetchSaved,
  };
}