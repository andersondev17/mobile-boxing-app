//track the searches made by user 
import { Exercise } from "@/interfaces/interfaces";
import { db } from '@/lib/db';
import { metrics } from '@/lib/db/schema';
import { and, desc, eq } from 'drizzle-orm';
import uuid from 'react-native-uuid';

export const updateSearchCount = async (query: string, exercise: Exercise): Promise<void> => { 
    try {
        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) return;

        // Check if a record of that search has already been stored
        const result = await db
            .select()
            .from(metrics)
            .where(
                and(
                    eq(metrics.search_term, normalizedQuery),
                    eq(metrics.exercise_id, exercise._id)
                )
            );

        if (result.length > 0) {
            // If a document is found increment the searchCount field
            const existingMetric = result[0];
            await db
                .update(metrics)
                .set({ 
                    count: existingMetric.count + 1,
                    updated_at: new Date()
                })
                .where(eq(metrics.id, existingMetric.id));
        } else {
            // If no document is found create a new document in SQLite database
            await db.insert(metrics).values({
                id: uuid.v4() as string,
                user_id: 'global', // Simple identifier for global metrics
                search_term: normalizedQuery,
                count: 1,
                poster_url: exercise.posterpath || 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png',
                exercise_id: exercise._id,
                title: exercise.title,
                created_at: new Date(),
                updated_at: new Date()
            });
        }
    } catch (error) {
        console.error('Error updating search count:', error);
    }
};

export const getTrendingExercises = async (limit: number = 10) => {
    try {
        const result = await db
            .select({
                search_term: metrics.search_term,
                title: metrics.title,
                count: metrics.count,
                poster_url: metrics.poster_url,
                exercise_id: metrics.exercise_id
            })
            .from(metrics)
            .orderBy(desc(metrics.count))
            .limit(limit);
        console.log('📊 Trending results:', result);
        return result;
    } catch (error) {
        console.error('Error fetching trending exercises:', error);
        return [];
    }
};