import { cleanOrphanMetrics } from '@/services/search';
import { drizzle } from 'drizzle-orm/expo-sqlite';
import { SQLiteProvider } from 'expo-sqlite';
import React, { ReactNode, Suspense } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import * as schema from '@/lib/db/schema';

interface DatabaseProviderProps {
    children: ReactNode;
}

async function initializeDatabase(db: any) {
    try {
        await db.execAsync(`
            CREATE TABLE IF NOT EXISTS app_metadata (
                id text PRIMARY KEY NOT NULL,
                database_version integer DEFAULT 1 NOT NULL,
                seeded_at integer,
                created_at integer DEFAULT (strftime('%s','now')) NOT NULL
            );

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

        const CURRENT_SEED_VERSION = 2; // Incrementa esto para forzar re-seed
        const metaCheck = await db.getAllAsync("SELECT database_version FROM app_metadata WHERE id = 'app_config'") as { database_version: number }[];
        const currentVersion = metaCheck.length > 0 ? metaCheck[0].database_version : 0;

        if (currentVersion < CURRENT_SEED_VERSION) {
            console.log(`🔄 Updating seed from version ${currentVersion} to ${CURRENT_SEED_VERSION}`);
            await db.execAsync("DELETE FROM exercises");
            const { seedExercises } = await import('@/lib/db/seed');
            const drizzleDb = drizzle(db, { schema });
            await seedExercises(drizzleDb);

            if (metaCheck.length === 0) {
                await db.execAsync(`INSERT INTO app_metadata (id, database_version, seeded_at) VALUES ('app_config', ${CURRENT_SEED_VERSION}, strftime('%s','now'))`);
            } else {
                await db.execAsync(`UPDATE app_metadata SET database_version = ${CURRENT_SEED_VERSION}, seeded_at = strftime('%s','now') WHERE id = 'app_config'`);
            }
        }

        await cleanOrphanMetrics();
        console.log('✅ Database initialized successfully');
    } catch (error) {
        console.error('❌ Database initialization error:', error);
        throw error;
    }
}

function LoadingFallback() {
    return (
        <View className="flex-1 justify-center items-center bg-gymshock-dark-900">
            <ActivityIndicator size="large" color="#FF4500" />
            <Text className="text-light-200 mt-3 text-base">Initializing database...</Text>
        </View>
    );
}

export function DatabaseProvider({ children }: DatabaseProviderProps) {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <SQLiteProvider
                databaseName="boxing_app.db"
                onInit={initializeDatabase}
                useSuspense
            >
                {children}
            </SQLiteProvider>
        </Suspense>
    );
}