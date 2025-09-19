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

        // Crear CADA tabla independientemente
        await expoDb.execAsync(`
            CREATE TABLE IF NOT EXISTS users (
                id text PRIMARY KEY NOT NULL,
                name text,
                email text NOT NULL,
                email_verified integer DEFAULT false NOT NULL,
                image text,
                role text DEFAULT 'enthusiast' NOT NULL,
                created_at integer NOT NULL,
                updated_at integer NOT NULL
            );

            CREATE TABLE IF NOT EXISTS exercises (
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

            CREATE TABLE IF NOT EXISTS metrics (
                id text PRIMARY KEY NOT NULL,
                user_id text NOT NULL,
                search_term text NOT NULL,
                count integer DEFAULT 0 NOT NULL,
                poster_url text NOT NULL,
                exercise_id text,
                title text NOT NULL,
                created_at integer DEFAULT (strftime('%s','now')) NOT NULL,
                updated_at integer DEFAULT (strftime('%s','now')) NOT NULL
            );
        `);

        const dataCheck = await expoDb.getAllAsync("SELECT COUNT(*) as count FROM exercises") as { count: number }[];
        if (dataCheck[0].count > 0) return;

        const { seedExercises } = await import('./seed');
        await seedExercises();
        console.log('Database setup complete');
    } catch (error) {
        console.error('Error seeding database:', error);
        throw error;
    }
}