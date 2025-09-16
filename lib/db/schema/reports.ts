import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import z from 'zod';
import { trainings } from './trainings';
import { users } from './users';
interface ProgressData {
    calories?: number;
    punches?: number;
    accuracy?: number;
    duration?: number;
    heartRate?: { avg: number; max: number; zones: Record<string, number> };
    steps?: number;
    distanceMeters?: number;
    formScore?: number;
    techniqueBreakdown?: Record<string, number>;
}

export const reports = sqliteTable('reports', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    training_id: text('training_id').references(() => trainings.id),
    progress_data: text('progress_data', { mode: 'json' }).$type<ProgressData>().notNull(),
    generated_at: integer('generated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const reportsRelations = relations(reports, ({ one }) => ({
    user: one(users, {
        fields: [reports.user_id],
        references: [users.id],
    }),
    training: one(trainings, {
        fields: [reports.training_id],
        references: [trainings.id],
    }),
}));

const progressDataSchema = z.object({
    calories: z.number().min(0).optional(),
    punches: z.number().min(0).optional(),
    accuracy: z.number().min(0).max(100).optional(),
    duration: z.number().min(0).optional(),
    heartRate: z.object({
        avg: z.number().min(0),
        max: z.number().min(0),
        zones: z.record(z.string(), z.number())
    }).optional(),
    steps: z.number().min(0).optional(),
    distanceMeters: z.number().min(0).optional(),
    formScore: z.number().min(0).max(100).optional(),
    techniqueBreakdown: z.record(z.string(), z.number()).optional()
});

export const reportsInsertSchema = createInsertSchema(reports, {
    user_id: z.string().uuid(),
    training_id: z.string().uuid().nullable(),
    progress_data: progressDataSchema,
});

export const reportsSelectSchema = createSelectSchema(reports);
export type InsertReport = z.infer<typeof reportsInsertSchema>;
export type SelectReport = z.infer<typeof reportsSelectSchema>;

