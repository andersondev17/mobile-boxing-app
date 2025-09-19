import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { users } from './users';

export const accounts = sqliteTable('accounts', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4()),
  user_id: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  provider_id: text('provider_id').notNull(),
  account_id: text('account_id').notNull(),
  access_token: text('access_token'),
  refresh_token: text('refresh_token'),
  access_token_expires_at: integer('access_token_expires_at', { mode: 'timestamp' }),
  refresh_token_expires_at: integer('refresh_token_expires_at', { mode: 'timestamp' }),
  password: text('password'),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const accountsRelations = relations(accounts, ({ one }) => ({
  user: one(users, {
    fields: [accounts.user_id],
    references: [users.id],
  }),
}));

export const accountsInsertSchema = createInsertSchema(accounts, {
  user_id: z.string().uuid(),
  provider_id: z.string().min(1),
  account_id: z.string().min(1),
  access_token: z.string().nullable(),
  refresh_token: z.string().nullable(),
  password: z.string().nullable(),
});

export const accountsSelectSchema = createSelectSchema(accounts);
export type InsertAccount = z.infer<typeof accountsInsertSchema>;
export type SelectAccount = z.infer<typeof accountsSelectSchema>;