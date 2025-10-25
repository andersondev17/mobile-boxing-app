import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import { z } from 'zod';

export const verifications = sqliteTable('verifications', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  identifier: text('identifier').notNull(), // usually email
  value: text('value').notNull(),
  expires_at: integer('expires_at', { mode: 'timestamp' }).notNull(),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const verificationsInsertSchema = createInsertSchema(verifications, {
  identifier: z.string().email(),
  value: z.string().min(1),
  expires_at: z.date(),
});

export const verificationsSelectSchema = createSelectSchema(verifications);
export type InsertVerification = z.infer<typeof verificationsInsertSchema>;
export type SelectVerification = z.infer<typeof verificationsSelectSchema>;

// ---