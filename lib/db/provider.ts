import { drizzle } from 'drizzle-orm/expo-sqlite';
import { openDatabaseSync } from 'expo-sqlite';
import { createContext } from 'react';
import * as schema from './schema';

// Database instance
const expoDb = openDatabaseSync('boxing_app.db');
export const db = drizzle(expoDb, { schema, logger: __DEV__ });

// Context for database access
export const DatabaseContext = createContext<typeof db | null>(null);

export type Database = typeof db;

// Hook to use database
export function useDatabase() {
    const React = require('react');
    const database = React.useContext(DatabaseContext);
    if (!database) {
        throw new Error('useDatabase must be used within DatabaseProvider');
    }
    return database;
}

// Initial data seeding
export async function seedInitialData() {
    try {
        const { seedDatabase } = await import('./seed');
        await seedDatabase();
        console.log('Database seeded successfully');
    } catch (error) {
        console.error('Error seeding database:', error);
        throw error;
    }
}