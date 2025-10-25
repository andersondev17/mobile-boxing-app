import { defineConfig } from 'drizzle-kit';

export default defineConfig({
    schema: './lib/db/schema/index.ts',
    out: './lib/db/migrations',
    dialect: 'sqlite',
    dbCredentials: {
        url: './boxing_app.db'
    },
    verbose: true,
    strict: true,
});