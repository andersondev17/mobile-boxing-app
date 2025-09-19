import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { users } from './users';

export const sessions = sqliteTable('sessions', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4()),
  user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token: text('token').notNull().unique(),
  ip_address: text('ip_address'),
  user_agent: text('user_agent'),
  expires_at: integer('expires_at', { mode: 'timestamp' }).notNull(),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const sessionsRelations = relations(sessions, ({ one }) => ({
  user: one(users, {
    fields: [sessions.user_id],
    references: [users.id],
  }),
}));

export const sessionsInsertSchema = createInsertSchema(sessions, {
  user_id: z.string().uuid(),
  token: z.string().min(1),
  ip_address: z.string().nullable(),
  user_agent: z.string().nullable(),
  expires_at: z.date(),
});

export const sessionsSelectSchema = createSelectSchema(sessions);

export type InsertSession = z.infer<typeof sessionsInsertSchema>;
export type SelectSession = z.infer<typeof sessionsSelectSchema>;