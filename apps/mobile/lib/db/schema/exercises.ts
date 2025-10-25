import { relations, sql } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { difficultyEnumZ, exerciseCategoryEnumZ } from './enums';


export const exercises = sqliteTable('exercises', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4() as string),
  title: text('title').notNull(),
  poster_url: text('poster_url').notNull(),
  category: text('category').notNull(),
  difficulty: text('difficulty').notNull().default('beginner'),
  duration_min: integer('duration_min').notNull(),
  description: text('description').notNull(),
  technique: text('technique').notNull(),
  muscles: text('muscles', { mode: 'json' }).$type<string[]>().notNull(),
  equipment: text('equipment'),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(strftime('%s','now'))`),
});

export const exerciseFilters = sqliteTable('exercise_filters', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4() as string),
  name: text('name').notNull().unique(),
  description: text('description'),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(strftime('%s','now'))`),
});

export const exerciseReviews = sqliteTable('exercise_reviews', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4() as string),
  user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  exercise_id: text('exercise_id').notNull().references(() => exercises.id, { onDelete: 'cascade' }),
  rating: integer('rating').notNull(),
  comment: text('comment'),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(strftime('%s','now'))`),
});

// Relations
export const exercisesRelations = relations(exercises, ({ many }) => ({
  reviews: many(exerciseReviews),
  trainingExercises: many(trainingExercises),
  metrics: many(metrics),
}));

export const exerciseReviewsRelations = relations(exerciseReviews, ({ one }) => ({
  user: one(users, {
    fields: [exerciseReviews.user_id],
    references: [users.id],
  }),
  exercise: one(exercises, {
    fields: [exerciseReviews.exercise_id],
    references: [exercises.id],
  }),
}));

// Zod schemas
export const exercisesInsertSchema = createInsertSchema(exercises, {
  title: z.string().min(2, 'Title must be at least 2 characters'),
  poster_url: z.string().url('Invalid poster URL'),
  category: exerciseCategoryEnumZ,
  difficulty: difficultyEnumZ.default('beginner'),
  duration_min: z.number().int().min(1, 'Duration must be at least 1 minute'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  technique: z.string().min(10, 'Technique must be at least 10 characters'),
  muscles: z.array(z.string()).min(1, 'At least one muscle group required'),
  equipment: z.string().nullable(),
});

export const exercisesSelectSchema = createSelectSchema(exercises);

export const exerciseFiltersInsertSchema = createInsertSchema(exerciseFilters, {
  name: z.string().min(2, 'Filter name must be at least 2 characters'),
  description: z.string().nullable(),
});

export const exerciseFiltersSelectSchema = createSelectSchema(exerciseFilters);

export const exerciseReviewsInsertSchema = createInsertSchema(exerciseReviews, {
  user_id: z.string().uuid(),
  exercise_id: z.string().uuid(),
  rating: z.number().int().min(1).max(5, 'Rating must be between 1 and 5'),
  comment: z.string().max(500, 'Comment cannot exceed 500 characters').nullable(),
});

export const exerciseReviewsSelectSchema = createSelectSchema(exerciseReviews);

export type InsertExercise = z.infer<typeof exercisesInsertSchema>;
export type SelectExercise = z.infer<typeof exercisesSelectSchema>;
export type InsertExerciseFilter = z.infer<typeof exerciseFiltersInsertSchema>;
export type SelectExerciseFilter = z.infer<typeof exerciseFiltersSelectSchema>;
export type InsertExerciseReview = z.infer<typeof exerciseReviewsInsertSchema>;
export type SelectExerciseReview = z.infer<typeof exerciseReviewsSelectSchema>;

// Forward declarations
import { metrics } from './metrics';
import { trainingExercises } from './trainings';
import { users } from './users';

