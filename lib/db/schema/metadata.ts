export const appMetadata = sqliteTable('app_metadata', {
    id: text('id').primaryKey().$defaultFn(() => 'app_config'),
    database_version: integer('database_version').notNull().default(1),
    seeded_at: integer('seeded_at', { mode: 'timestamp' }),
    created_at: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(strftime('%s','now'))`),
});