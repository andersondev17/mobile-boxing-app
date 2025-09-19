
import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { exercises } from './exercises';
import { users } from './users';


export const metrics = sqliteTable('metrics', {
    id: text('id').primaryKey().$defaultFn(() => uuid.v4()),
    user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    search_term: text('search_term').notNull(),
    count: integer('count').notNull().default(0),
    poster_url: text('poster_url').notNull(),
    exercise_id: text('exercise_id').references(() => exercises.id),
    title: text('title').notNull(),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const metricsRelations = relations(metrics, ({ one }) => ({
    user: one(users, {
        fields: [metrics.user_id],
        references: [users.id],
    }),
    exercise: one(exercises, {
        fields: [metrics.exercise_id],
        references: [exercises.id],
    }),
}));

export const metricsInsertSchema = createInsertSchema(metrics, {
    user_id: z.string().uuid(),
    search_term: z.string().min(1),
    count: z.number().int().min(0).default(0),
    poster_url: z.string().url(),
    exercise_id: z.string().uuid().nullable(),
    title: z.string().min(1),
});

export const metricsSelectSchema = createSelectSchema(metrics);
export type InsertMetric = z.infer<typeof metricsInsertSchema>;
export type SelectMetric = z.infer<typeof metricsSelectSchema>;
