import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import z from 'zod';
import { users } from './users';
export const achievements = sqliteTable('achievements', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    name: text('name').notNull(),
    description: text('description').notNull(),
    icon_url: text('icon_url'),
    unlocked_at: integer('unlocked_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const achievementsRelations = relations(achievements, ({ one }) => ({
    user: one(users, {
        fields: [achievements.user_id],
        references: [users.id],
    }),
}));

export const achievementsInsertSchema = createInsertSchema(achievements, {
    user_id: z.string().uuid(),
    name: z.string().min(2),
    description: z.string().min(10),
    icon_url: z.string().url().nullable(),
});

export const achievementsSelectSchema = createSelectSchema(achievements);
export type InsertAchievement = z.infer<typeof achievementsInsertSchema>;
export type SelectAchievement = z.infer<typeof achievementsSelectSchema>;
