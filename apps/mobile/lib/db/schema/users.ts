import { relations } from 'drizzle-orm';
import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import uuid from 'react-native-uuid';
import { z } from 'zod';
import { roleEnumZ } from './enums';


export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => uuid.v4()),
  name: text('name'),
  email: text('email').notNull().unique(),
  email_verified: integer('email_verified', { mode: 'boolean' }).notNull().default(false),
  image: text('image'),
  role: text('role').notNull().default('enthusiast'),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

// Zod schemas
export const usersInsertSchema = createInsertSchema(users, {
  id: z.string().uuid().optional(),
  name: z.string().min(2).nullable(),
  email: z.string().email(),
  email_verified: z.boolean().optional(),
  image: z.string().url().nullable(),
  role: roleEnumZ.default('enthusiast'),
});

export const usersSelectSchema = createSelectSchema(users);

export type InsertUser = z.infer<typeof usersInsertSchema>;
export type SelectUser = z.infer<typeof usersSelectSchema>;

// Relations simplified to avoid circular imports
export const usersRelations = relations(users, ({ many }) => ({
  sessions: many(sessions),
  accounts: many(accounts),
}));

// Forward declarations
import { accounts } from './accounts';
import { sessions } from './sessions';

