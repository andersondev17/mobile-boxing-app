import { db } from '@/lib/db';
import { exercises } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import uuid from 'react-native-uuid';

const exerciseData = [
  {
    title: 'Jab',
    poster_url: 'https://media.giphy.com/media/ovzh1nMQQMOMXE3WVx/giphy.gif',
    category: 'golpes_basicos',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Golpe directo rápido con la mano adelantada',
    technique: 'Mantén la mano alta, extiende el brazo rápidamente y retira inmediatamente a la posición de guardia. Gira la palma hacia abajo al impactar:cite[4].',
    muscles: ['Hombros', 'Tríceps', 'Core'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  },
  {
    title: 'Cross (Directo de Derecha)',
    poster_url: 'https://media.giphy.com/media/xUySTxL9fZyjIKzoLS/giphy.gif',
    category: 'golpes_basicos',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Golpe potente con la mano trasera',
    technique: 'Gira la cadera y los hombros mientras transfieres el peso al pie delantero. Mantén la mano derecha protegiendo el mentón:cite[9].',
    muscles: ['Hombros', 'Espalda', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  },
  {
    title: 'Gancho Izquierdo (Left Hook)',
    poster_url: 'https://media.giphy.com/media/lmHf50zYQPAYmHvTGR/giphy.gif',
    category: 'golpes_circulares',
    difficulty: 'intermedio',
    duration_min: 6,
    description: 'Golpe circular con la mano izquierda al rostro',
    technique: 'Mantén el codo a 90°, gira el torso y pivota el pie izquierdo. El movimiento viene de la rotación corporal:cite[9].',
    muscles: ['Hombros', 'Oblicuos', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  },
  {
    title: 'Gancho al Cuerpo (Body Hook)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'golpes_circulares',
    difficulty: 'intermedio',
    duration_min: 7,
    description: 'Golpe circular al área corporal del oponente',
    technique: 'Flexiona ligeramente las rodillas y gira el torso para generar potencia. Mantén la otra mano protegiendo el rostro.',
    muscles: ['Oblicuos', 'Core', 'Hombros'],
    equipment: 'Saco de boxeo, pads o sparring'
  },
  {
    title: 'Uppercut (Gancho Vertical)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'golpes_potencia',
    difficulty: 'intermedio',
    duration_min: 7,
    description: 'Golpe ascendente dirigido al mentón',
    technique: 'Dobla las rodillas y empuja desde las piernas con un movimiento ascendente. Mantén el codo flexionado:cite[9].',
    muscles: ['Piernas', 'Glúteos', 'Core', 'Hombros', 'Bíceps'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  },
  {
    title: 'Jab-Doble',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'combinaciones',
    difficulty: 'intermedio',
    duration_min: 8,
    description: 'Dos jabs rápidos consecutivos',
    technique: 'Ejecuta un jab rápido y sigue inmediatamente con un segundo jab. Mantén la velocidad y recuperación:cite[4].',
    muscles: ['Hombros', 'Tríceps', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  },
  {
    title: 'Cruzado-Jab (1-2)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'combinaciones',
    difficulty: 'principiante',
    duration_min: 8,
    description: 'Combinación básica de jab seguido de cruzado',
    technique: 'Jab rápido seguido de un cruzado potente con la mano trasera. Transfiere el peso adecuadamente:cite[9].',
    muscles: ['Hombros', 'Tríceps', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o shadow boxing'
  }
];
const defensiveExercises = [
  {
    title: 'Slip (Esquiva Lateral)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 5,
    description: 'Esquivar golpes moviendo la cabeza',
    technique: 'Desplaza la cabeza ligeramente hacia los lados manteniendo la guardia alta. Movimiento pequeño y eficiente.',
    muscles: ['Cuello', 'Core', 'Oblicuos'],
    equipment: 'Ninguno o trabajo con compañero'
  },
  {
    title: 'Bob and Weave (Agachada y Movimiento)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 6,
    description: 'Movimiento de agacharse y esquivar',
    technique: 'Agáchate flexionando rodillas y muévete en forma de U debajo del golpe. Mantén el equilibrio:cite[4].',
    muscles: ['Piernas', 'Core', 'Glúteos'],
    equipment: 'Ninguno o trabajo con compañero'
  },
  {
    title: 'Block (Bloqueo)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Bloquear golpes con los guantes y brazos',
    technique: 'Usa los guantes y brazos para absorber el impacto de los golpes manteniendo las manos cerca del rostro.',
    muscles: ['Brazos', 'Hombros', 'Core'],
    equipment: 'Guantes de boxeo'
  },
  {
    title: 'Parry (Desvío)',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 5,
    description: 'Desviar golpes con movimientos precisos',
    technique: 'Usa movimientos pequeños de manos para desviar golpes. Requiere timing y precisión.',
    muscles: ['Antebrazos', 'Hombros', 'Reflejos'],
    equipment: 'Guantes de boxeo'
  }
];
const strengthExercises = [
  {
    title: 'Saltar Cuerda',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'acondicionamiento',
    difficulty: 'principiante',
    duration_min: 10,
    description: 'Salto de cuerda para condición física',
    technique: 'Mantén un ritmo constante con saltos ligeros sobre las puntas de los pies. Variar patrones de salto.',
    muscles: ['Pantorrillas', 'Cardiovascular', 'Coordinación'],
    equipment: 'Cuerda para saltar'
  },
  {
    title: 'Sombra con Pesas Ligeras',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'acondicionamiento',
    difficulty: 'intermedio',
    duration_min: 10,
    description: 'Boxeo de sombra con pesas para resistencia',
    technique: 'Ejecuta combinaciones de boxeo con pesas ligeras (1-2 kg). Enfócate en técnica y no en velocidad.',
    muscles: ['Hombros', 'Resistencia muscular', 'Core'],
    equipment: 'Pesas ligeras'
  },
  {
    title: 'Plancha con Golpes',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fortalecimiento_core',
    difficulty: 'avanzado',
    duration_min: 5,
    description: 'Ejercicio de core con movimiento de golpes',
    technique: 'En posición de plancha, ejecuta golpes alternados manteniendo la estabilidad corporal.',
    muscles: ['Core', 'Hombros', 'Estabilidad'],
    equipment: 'Tapete de ejercicio'
  },
  {
    title: 'Giros Rusos con Pesas',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fortalecimiento_core',
    difficulty: 'intermedio',
    duration_min: 7,
    description: 'Fortalecimiento de oblicuos para rotación',
    technique: 'Sentado con rodillas flexionadas, gira el torso con pesa o balón medicinal. Controla el movimiento.',
    muscles: ['Oblicuos', 'Core', 'Rotación'],
    equipment: 'Pesa o balón medicinal'
  }
];
export const seedExercises = async () => {
  try {
    // Combinar todos los ejercicios
    const allExercises = [...exerciseData, ...defensiveExercises, ...strengthExercises];

    // Para cada ejercicio, verificar si existe por título y categoría
    for (const exercise of allExercises) {
      const existingExercise = await db.select()
        .from(exercises)
        .where(eq(exercises.title, exercise.title))
        .limit(1);

      if (existingExercise.length === 0) {
        await db.insert(exercises).values({
          id: uuid.v4() as string,
          ...exercise
        });
      }
    }

  } catch (error) {
    console.error('Error en seeding de ejercicios:', error);
  }
}; 