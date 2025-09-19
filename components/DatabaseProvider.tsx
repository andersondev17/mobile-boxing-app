import { DatabaseContext, db, seedInitialData } from '@/lib/db/provider';
import React, { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';

interface DatabaseStatusType {
    isInitialized: boolean;
    error: Error | null;
}

const DatabaseStatusContext = createContext<DatabaseStatusType>({
    isInitialized: false,
    error: null,
});

export const useDatabaseStatus = () => useContext(DatabaseStatusContext);

interface DatabaseProviderProps {
    children: ReactNode;
}

export function DatabaseProvider({ children }: DatabaseProviderProps) {
    const [isInitialized, setIsInitialized] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        async function setupDatabase() {
            try {

                // Execute seed using your existing function
                await seedInitialData();

                if (isMounted) {
                    setIsInitialized(true);
                    setLoading(false);
                }
            } catch (err) {
                console.error('Database initialization error:', err);
                if (isMounted) {
                    setError(err instanceof Error ? err : new Error('Unknown database error'));
                    setLoading(false);
                }
            }
        }

        setupDatabase();

        return () => {
            isMounted = false;
        };
    }, []);

    if (loading) {
        return (
            <View className="flex-1 justify-center items-center bg-gymshock-dark-900">
                <ActivityIndicator size="large" color="#FF4500" />
                <Text className="text-light-200 mt-3 text-base">Initializing database...</Text>
            </View>
        );
    }

    if (error) {
        return (
            <View className="flex-1 justify-center items-center p-5 bg-gymshock-dark-900">
                <Text className="text-lg font-bold text-red-500 mb-2">Database Error</Text>
                <Text className="text-sm text-red-400 text-center">{error.message}</Text>
            </View>
        );
    }

    return (
        <DatabaseStatusContext.Provider value={{ isInitialized, error }}>
            <DatabaseContext.Provider value={db}>
                {children}
            </DatabaseContext.Provider>
        </DatabaseStatusContext.Provider>
    );
}