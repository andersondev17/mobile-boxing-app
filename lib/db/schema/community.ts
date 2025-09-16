import { integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import { z } from 'zod';

export const communityPosts = sqliteTable('community_posts', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    user_id: text('user_id').notNull(),
    content: text('content').notNull(),
    image_url: text('image_url'),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
    updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const communityComments = sqliteTable('community_comments', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    post_id: text('post_id').notNull(),
    user_id: text('user_id').notNull(),
    content: text('content').notNull(),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const communityLikes = sqliteTable('community_likes', {
    id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
    post_id: text('post_id').notNull(),
    user_id: text('user_id').notNull(),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const communityPostsInsertSchema = createInsertSchema(communityPosts, {
    user_id: z.string().uuid(),
    content: z.string().min(1).max(2000),
    image_url: z.string().url().nullable(),
});

export const communityPostsSelectSchema = createSelectSchema(communityPosts);
export type InsertCommunityPost = z.infer<typeof communityPostsInsertSchema>;
export type SelectCommunityPost = z.infer<typeof communityPostsSelectSchema>;