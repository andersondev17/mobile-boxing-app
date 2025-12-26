import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import uuid from 'react-native-uuid';

import { exercises } from './exercises';
import { users } from './users';

export const savedExercises = sqliteTable('saved_exercises', {
    id: text('id')
        .primaryKey()
        .$defaultFn(() => uuid.v4() as string),

    user_id: text('user_id')
        .notNull()
        .references(() => users.id, { onDelete: 'cascade' }),

    exercise_id: text('exercise_id')
        .notNull()
        .references(() => exercises.id, { onDelete: 'cascade' }),

    saved_at: integer('saved_at', { mode: 'timestamp' })
        .notNull()
        .$defaultFn(() => new Date()),
});

export const savedExercisesRelations = relations(
    savedExercises,
    ({ one }) => ({
        user: one(users, {
            fields: [savedExercises.user_id],
            references: [users.id],
        }),
        exercise: one(exercises, {
            fields: [savedExercises.exercise_id],
            references: [exercises.id],
        }),
    })
);


export type SavedExercise = typeof savedExercises.$inferSelect;
export type NewSavedExercise = typeof savedExercises.$inferInsert;

