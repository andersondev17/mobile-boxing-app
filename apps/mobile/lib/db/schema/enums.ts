import { z } from 'zod';

/**
 * Zod enums for validation. SQLite stores as TEXT with CHECK constraints.
 */
export const roleEnumZ = z.enum(['enthusiast', 'trainer', 'admin']);
export type Role = z.infer<typeof roleEnumZ>;

export const difficultyEnumZ = z.enum(['beginner', 'intermediate', 'advanced']);
export type Difficulty = z.infer<typeof difficultyEnumZ>;

export const trainingStatusEnumZ = z.enum(['planned', 'in_progress', 'completed', 'cancelled']);
export type TrainingStatus = z.infer<typeof trainingStatusEnumZ>;

export const exerciseCategoryEnumZ = z.enum([
    'basic_punches',
    'combinations',
    'defense',
    'footwork',
    'conditioning',
    'advanced_techniques'
]);
export type ExerciseCategory = z.infer<typeof exerciseCategoryEnumZ>;