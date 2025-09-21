import { db } from '@/lib/db';
import { exercises } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import uuid from 'react-native-uuid';

const tecnicasGolpeoData = [
  {
    title: 'Jab',
    poster_url: 'https://media.giphy.com/media/ovzh1nMQQMOMXE3WVx/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Golpe directo rápido con la mano adelantada',
    technique: 'Mantén la guardia alta, extiende el brazo rápidamente y retira inmediatamente. Gira la palma hacia abajo al impactar.',
    muscles: ['Hombros', 'Tríceps', 'Core'],
    equipment: 'Saco de boxeo, pads o sombra'
  },
  {
    title: 'Directo de Derecha',
    poster_url: 'https://media.giphy.com/media/xUySTxL9fZyjIKzoLS/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Golpe potente con la mano trasera',
    technique: 'Gira la cadera y hombros mientras transfieres peso al pie delantero. Mantén la mano protegiendo el mentón.',
    muscles: ['Hombros', 'Espalda', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o sombra'
  },
  {
    title: 'Gancho Izquierdo',
    poster_url: 'https://media.giphy.com/media/lmHf50zYQPAYmHvTGR/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'intermedio',
    duration_min: 6,
    description: 'Golpe circular con la mano izquierda al rostro',
    technique: 'Mantén el codo a 90°, gira el torso y pivota el pie izquierdo. El movimiento viene de la rotación corporal.',
    muscles: ['Hombros', 'Oblicuos', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o sombra'
  },
  {
    title: 'Gancho al Cuerpo',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'intermedio',
    duration_min: 7,
    description: 'Golpe circular dirigido al área corporal',
    technique: 'Flexiona las rodillas y gira el torso para generar potencia. Mantén la otra mano protegiendo el rostro.',
    muscles: ['Oblicuos', 'Core', 'Hombros'],
    equipment: 'Saco de boxeo, pads o sparring'
  },
  {
    title: 'Uppercut',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'intermedio',
    duration_min: 7,
    description: 'Golpe ascendente dirigido al mentón',
    technique: 'Dobla las rodillas y empuja desde las piernas con movimiento ascendente. Mantén el codo flexionado.',
    muscles: ['Piernas', 'Glúteos', 'Core', 'Hombros', 'Bíceps'],
    equipment: 'Saco de boxeo, pads o sombra'
  },
  {
    title: 'Combinación 1-2',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'principiante',
    duration_min: 8,
    description: 'Jab seguido de directo de derecha',
    technique: 'Jab rápido seguido de directo potente con la mano trasera. Transfiere el peso adecuadamente.',
    muscles: ['Hombros', 'Tríceps', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o sombra'
  },
  {
    title: 'Doble Jab',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'tecnicas_golpeo',
    difficulty: 'intermedio',
    duration_min: 8,
    description: 'Dos jabs rápidos consecutivos',
    technique: 'Ejecuta un jab rápido y sigue inmediatamente con segundo jab. Mantén velocidad y recuperación.',
    muscles: ['Hombros', 'Tríceps', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo, pads o sombra'
  }
];

const tecnicasDefensaData = [
  {
    title: 'Esquiva Lateral',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 5,
    description: 'Esquivar golpes moviendo la cabeza lateralmente',
    technique: 'Desplaza la cabeza ligeramente hacia los lados manteniendo la guardia alta. Movimiento pequeño y eficiente.',
    muscles: ['Cuello', 'Core', 'Oblicuos'],
    equipment: 'Ninguno o trabajo con compañero'
  },
  {
    title: 'Agachada y Tejido',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 6,
    description: 'Agacharse y moverse en forma de U para esquivar',
    technique: 'Agáchate flexionando rodillas y muévete en U por debajo del golpe. Mantén el equilibrio.',
    muscles: ['Piernas', 'Core', 'Glúteos'],
    equipment: 'Ninguno o trabajo con compañero'
  },
  {
    title: 'Bloqueo con Guantes',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'principiante',
    duration_min: 5,
    description: 'Bloquear golpes con guantes y brazos',
    technique: 'Usa los guantes y brazos para absorber el impacto manteniendo las manos cerca del rostro.',
    muscles: ['Brazos', 'Hombros', 'Core'],
    equipment: 'Guantes de boxeo'
  },
  {
    title: 'Desvío',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'defensa',
    difficulty: 'intermedio',
    duration_min: 5,
    description: 'Desviar golpes con movimientos precisos de manos',
    technique: 'Usa movimientos pequeños de manos para desviar golpes. Requiere timing y precisión perfectos.',
    muscles: ['Antebrazos', 'Hombros', 'Reflejos'],
    equipment: 'Guantes de boxeo'
  }
];

const ejerciciosFuerzaData = [
  {
    title: 'Saltar Cuerda',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fuerza_acondicionamiento',
    difficulty: 'principiante',
    duration_min: 10,
    description: 'Salto de cuerda para condición cardiovascular',
    technique: 'Mantén ritmo constante con saltos ligeros sobre las puntas. Varía patrones de salto.',
    muscles: ['Pantorrillas', 'Cardiovascular', 'Coordinación'],
    equipment: 'Cuerda para saltar'
  },
  {
    title: 'Sombra con Pesas',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fuerza_acondicionamiento',
    difficulty: 'intermedio',
    duration_min: 10,
    description: 'Boxeo de sombra con pesas ligeras para resistencia',
    technique: 'Ejecuta combinaciones con pesas ligeras (1-2 kg). Enfócate en técnica, no en velocidad.',
    muscles: ['Hombros', 'Resistencia muscular', 'Core'],
    equipment: 'Pesas ligeras de 1-2 kg'
  },
  {
    title: 'Plancha con Golpes',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fuerza_acondicionamiento',
    difficulty: 'avanzado',
    duration_min: 5,
    description: 'Ejercicio de core con movimientos de golpes',
    technique: 'En posición de plancha, ejecuta golpes alternados manteniendo estabilidad corporal.',
    muscles: ['Core', 'Hombros', 'Estabilidad'],
    equipment: 'Tapete de ejercicio'
  },
  {
    title: 'Giros Rusos',
    poster_url: 'https://media.giphy.com/media/3o7TKsQ8UQ4l4LhGz6/giphy.gif',
    category: 'fuerza_acondicionamiento',
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
    const allExercises = [
      ...tecnicasGolpeoData, 
      ...tecnicasDefensaData, 
      ...ejerciciosFuerzaData
    ];

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