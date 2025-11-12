import { drizzle } from 'drizzle-orm/expo-sqlite';
import { useSQLiteContext } from 'expo-sqlite';
import * as schema from './schema';

export function useDatabase() {
    const database = useSQLiteContext();
    return drizzle(database, { schema, logger: __DEV__ });
}

export type Database = ReturnType<typeof useDatabase>;