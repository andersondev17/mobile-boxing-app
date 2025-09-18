import { drizzle } from 'drizzle-orm/expo-sqlite';
import * as SQLite from 'expo-sqlite';
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
        const expoDb = SQLite.openDatabaseSync('boxing_app.db');

        // Ejecutar manualmente la migración si la tabla no existe
        const tableCheck = await expoDb.getAllAsync(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exercises';"
        );

        if (tableCheck.length === 0) {
            // Ejecuta el SQL de la migracion
            await expoDb.execAsync(`
                CREATE TABLE exercises (
                    id text PRIMARY KEY NOT NULL,
                    title text NOT NULL,
                    poster_url text NOT NULL,
                    category text NOT NULL,
                    difficulty text DEFAULT 'beginner' NOT NULL,
                    duration_min integer NOT NULL,
                    description text NOT NULL,
                    technique text NOT NULL,
                    muscles text NOT NULL,
                    equipment text,
                    created_at integer DEFAULT (strftime('%s','now')) NOT NULL
                );
                -- ... otras tablas si son necesarias
            `);
            console.log('Migraciones aplicadas manualmente');
        }

        const { seedExercises } = await import('./seed');
        await seedExercises();
        console.log('Database seeded successfully');
    } catch (error) {
        console.error('Error seeding database:', error);
        throw error;
    }
}