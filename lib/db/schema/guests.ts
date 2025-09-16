import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import z from 'zod';

// lib/db/schema/auth/guests.ts
export const guests = sqliteTable('guests', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    session_token: text('session_token').notNull().unique(),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    expires_at: integer('expires_at', { mode: 'timestamp' }).notNull(),
});

export const guestsInsertSchema = createInsertSchema(guests, {
    session_token: z.string().min(1),
    expires_at: z.date(),
});

export const guestsSelectSchema = createSelectSchema(guests);
export type InsertGuest = z.infer<typeof guestsInsertSchema>;
export type SelectGuest = z.infer<typeof guestsSelectSchema>;