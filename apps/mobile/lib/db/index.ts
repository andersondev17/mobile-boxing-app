
// lib/db/index.ts - Expo SQLite Database Setup
import { drizzle } from 'drizzle-orm/expo-sqlite';
import { openDatabaseSync } from 'expo-sqlite';
import * as schema from './schema/index';

// Initialize SQLite database for Expo
const expoDb = openDatabaseSync('boxing_app.db');

// Create Drizzle instance with full schema
export const db = drizzle(expoDb, {
    schema,
    logger: __DEV__ // Only log in development
});

export type Database = typeof db;

// Export all schema types and tables
export * from './schema/index';
