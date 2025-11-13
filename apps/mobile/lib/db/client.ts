import { drizzle } from 'drizzle-orm/expo-sqlite';
import { openDatabaseSync } from 'expo-sqlite';
import * as schema from './schema';

let _cachedDb: ReturnType<typeof drizzle> | null = null;

export function getDb() {
    if (!_cachedDb) {
        const expoDb = openDatabaseSync('boxing_app.db');
        _cachedDb = drizzle(expoDb, { schema, logger: __DEV__ });
    }
    return _cachedDb;
}

export const db = new Proxy({} as ReturnType<typeof drizzle>, {
    get(_, prop) {
        return getDb()[prop as keyof ReturnType<typeof drizzle>];
    }
});
