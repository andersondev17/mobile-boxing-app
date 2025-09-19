import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { trainingStatusEnumZ } from './enums';


export const trainings = sqliteTable('trainings', {
    id: text('id').primaryKey().$defaultFn(() => uuid.v4()),
    user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    trainer_id: text('trainer_id').references(() => users.id),
    title: text('title').notNull(),
    notes: text('notes'),
    status: text('status').notNull().default('planned'),
    started_at: integer('started_at', { mode: 'timestamp' }),
    ended_at: integer('ended_at', { mode: 'timestamp' }),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const trainingExercises = sqliteTable('training_exercises', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    training_id: text('training_id').notNull().references(() => trainings.id, { onDelete: 'cascade' }),
    exercise_id: text('exercise_id').notNull().references(() => exercises.id, { onDelete: 'cascade' }),
    sets: integer('sets').notNull().default(1),
    reps: integer('reps').notNull().default(1),
    duration_seconds: integer('duration_seconds').notNull().default(0),
    order: integer('order').notNull().default(0),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

// Relations
export const trainingsRelations = relations(trainings, ({ one, many }) => ({
    user: one(users, {
        fields: [trainings.user_id],
        references: [users.id],
        relationName: 'userTrainings',
    }),
    trainer: one(users, {
        fields: [trainings.trainer_id],
        references: [users.id],
        relationName: 'trainerSessions',
    }),
    exercises: many(trainingExercises),
    reports: many(reports),
}));

export const trainingExercisesRelations = relations(trainingExercises, ({ one }) => ({
    training: one(trainings, {
        fields: [trainingExercises.training_id],
        references: [trainings.id],
    }),
    exercise: one(exercises, {
        fields: [trainingExercises.exercise_id],
        references: [exercises.id],
    }),
}));

// Zod schemas
export const trainingsInsertSchema = createInsertSchema(trainings, {
    user_id: z.string().uuid(),
    trainer_id: z.string().uuid().nullable(),
    title: z.string().min(2, 'Training title must be at least 2 characters'),
    notes: z.string().max(1000, 'Notes cannot exceed 1000 characters').nullable(),
    status: trainingStatusEnumZ.default('planned'),
    started_at: z.date().nullable(),
    ended_at: z.date().nullable(),
});

export const trainingsSelectSchema = createSelectSchema(trainings);

export const trainingExercisesInsertSchema = createInsertSchema(trainingExercises, {
    training_id: z.string().uuid(),
    exercise_id: z.string().uuid(),
    sets: z.number().int().min(1, 'Sets must be at least 1'),
    reps: z.number().int().min(1, 'Reps must be at least 1'),
    duration_seconds: z.number().int().min(0, 'Duration cannot be negative'),
    order: z.number().int().min(0, 'Order cannot be negative'),
});

export const trainingExercisesSelectSchema = createSelectSchema(trainingExercises);

export type InsertTraining = z.infer<typeof trainingsInsertSchema>;
export type SelectTraining = z.infer<typeof trainingsSelectSchema>;
export type InsertTrainingExercise = z.infer<typeof trainingExercisesInsertSchema>;
export type SelectTrainingExercise = z.infer<typeof trainingExercisesSelectSchema>;

// Forward declarations
import { exercises } from './exercises';
import { reports } from './reports';
import { users } from './users';

