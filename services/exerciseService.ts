// services/exerciseService.ts
import { Exercise } from '@/interfaces/interfaces'; // Use the shared interface
import { db } from '@/lib/db';
import { exercises } from '@/lib/db/schema';
import { eq, like, or } from 'drizzle-orm';

const CATEGORIES = {
    TECNICAS_GOLPEO: 'tecnicas_golpeo',
    DEFENSA: 'defensa',
    FUERZA_ACONDICIONAMIENTO: 'fuerza_acondicionamiento'
} as const;

export const fetchExercises = async ({ query }: { query: string }): Promise<Exercise[]> => {
    try {
        await new Promise(resolve => setTimeout(resolve, 300));

        const dbExercises = query.trim()
            ? await db
                .select()
                .from(exercises)
                .where(
                    or(
                        like(exercises.title, `%${query.toLowerCase()}%`),
                        like(exercises.category, `%${query.toLowerCase()}%`)
                    )
                )
            : await db.select().from(exercises);

        return dbExercises.map(ex => ({
            _id: ex.id,
            title: ex.title,
            posterpath: ex.poster_url,
            category: ex.category,
            difficulty: ex.difficulty,
            duration: `${ex.duration_min} min`,
            description: ex.description,
            technique: ex.technique,
            muscles: Array.isArray(ex.muscles) ? ex.muscles : JSON.parse(ex.muscles || '[]'),
            equipment: ex.equipment || ''
        }));
    } catch (error) {
        console.error('Error fetching exercises:', error);
        throw new Error('Failed to fetch exercises');
    }
};

export const fetchExerciseById = async (id: string): Promise<Exercise | null> => {
    try {
        const [dbExercise] = await db
            .select()
            .from(exercises)
            .where(eq(exercises.id, id))
            .limit(1);

        if (!dbExercise) return null;

        return {
            _id: dbExercise.id,
            title: dbExercise.title,
            posterpath: dbExercise.poster_url,
            category: dbExercise.category,
            difficulty: dbExercise.difficulty,
            duration: `${dbExercise.duration_min} min`,
            description: dbExercise.description,
            technique: dbExercise.technique,
            muscles: Array.isArray(dbExercise.muscles) ? dbExercise.muscles : JSON.parse(dbExercise.muscles || '[]'),
            equipment: dbExercise.equipment || ''
        };
    } catch (error) {
        console.error('Error fetching exercise by ID:', error);
        throw new Error('Failed to fetch exercise details');
    }
};

export const fetchTecnicasGolpeo = async (): Promise<Exercise[]> => {
    try {
        const dbExercises = await db
            .select()
            .from(exercises)
            .where(eq(exercises.category, CATEGORIES.TECNICAS_GOLPEO));

        return dbExercises.map(ex => ({
            _id: ex.id,
            title: ex.title,
            posterpath: ex.poster_url,
            category: ex.category,
            difficulty: ex.difficulty,
            duration: `${ex.duration_min} min`,
            description: ex.description,
            technique: ex.technique,
            muscles: Array.isArray(ex.muscles) ? ex.muscles : JSON.parse(ex.muscles || '[]'),
            equipment: ex.equipment || ''
        }));
    } catch (error) {
        console.error('Error fetching técnicas de golpeo:', error);
        throw new Error('Failed to fetch técnicas de golpeo');
    }
};

export const fetchTecnicasDefensa = async (): Promise<Exercise[]> => {
    try {
        const dbExercises = await db
            .select()
            .from(exercises)
            .where(eq(exercises.category, CATEGORIES.DEFENSA));

        return dbExercises.map(ex => ({
            _id: ex.id,
            title: ex.title,
            posterpath: ex.poster_url,
            category: ex.category,
            difficulty: ex.difficulty,
            duration: `${ex.duration_min} min`,
            description: ex.description,
            technique: ex.technique,
            muscles: Array.isArray(ex.muscles) ? ex.muscles : JSON.parse(ex.muscles || '[]'),
            equipment: ex.equipment || ''
        }));
    } catch (error) {
        console.error('Error fetching técnicas de defensa:', error);
        throw new Error('Failed to fetch técnicas de defensa');
    }
};

export const fetchEjerciciosFuerza = async (): Promise<Exercise[]> => {
    try {
        const dbExercises = await db
            .select()
            .from(exercises)
            .where(eq(exercises.category, CATEGORIES.FUERZA_ACONDICIONAMIENTO));

        return dbExercises.map(ex => ({
            _id: ex.id,
            title: ex.title,
            posterpath: ex.poster_url,
            category: ex.category,
            difficulty: ex.difficulty,
            duration: `${ex.duration_min} min`,
            description: ex.description,
            technique: ex.technique,
            muscles: Array.isArray(ex.muscles) ? ex.muscles : JSON.parse(ex.muscles || '[]'),
            equipment: ex.equipment || ''
        }));
    } catch (error) {
        console.error('Error fetching ejercicios de fuerza:', error);
        throw new Error('Failed to fetch ejercicios de fuerza');
    }
};
