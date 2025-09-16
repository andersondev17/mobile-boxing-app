import { db } from './index';
import {
  achievements,
  exerciseFilters,
  exercises,
  users
} from './schema/index';

// Seed users with proper roles
const seedUsers = [
  {
    id: crypto.randomUUID(),
    name: 'Boxing Enthusiast',
    email: 'user@boxingapp.com',
    email_verified: true,
    role: 'enthusiast' as const,
    image: null
  },
  {
    id: crypto.randomUUID(), 
    name: 'Coach Mike',
    email: 'trainer@boxingapp.com',
    email_verified: true,
    role: 'trainer' as const,
    image: null
  },
  {
    id: crypto.randomUUID(),
    name: 'Admin User',
    email: 'admin@boxingapp.com', 
    email_verified: true,
    role: 'admin' as const,
    image: null
  }
];

// Migrated from BOXING_EXERCISES to SQLite format
const seedExercises = [
  {
    id: crypto.randomUUID(),
    title: 'Jab',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3c2dhcDM2dmIxNGhjcXBidGQ0cTRwdDhvNHR2NHFqcjA2anJpd2R6cyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ovzh1nMQQMOMXE3WVx/giphy.gif',
    category: 'basic_punches',
    difficulty: 'beginner' as const,
    duration_min: 5,
    description: 'Golpe directo con la mano adelantada',
    technique: 'Extiende el brazo adelantado en línea recta hacia el objetivo',
    muscles: ['Hombros', 'Tríceps', 'Core'],
    equipment: 'Saco de boxeo o pads'
  },
  {
    id: crypto.randomUUID(),
    title: 'Cross',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3NTRpYmllb2YwZGphNXowZGl6YzR2ZHF0aHZnM2NzMmR1ZmNoanprcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUySTxL9fZyjIKzoLS/giphy.gif',
    category: 'basic_punches',
    difficulty: 'beginner' as const,
    duration_min: 5,
    description: 'Golpe directo con la mano trasera',
    technique: 'Rota la cadera y pivotea el pie trasero al lanzar',
    muscles: ['Hombros', 'Espalda', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo o pads'
  },
  {
    id: crypto.randomUUID(),
    title: 'Hook',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZHM3Y3QzNjNoZGU4Z2dycHN0cTdia2Nzd3RnZXA0bzFuOWlvbDBxYSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/lmHf50zYQPAYmHvTGR/giphy.gif',
    category: 'combinations',
    difficulty: 'intermediate' as const,
    duration_min: 6,
    description: 'Golpe circular dirigido al costado del objetivo',
    technique: 'Mantén el codo alto y rota desde la cadera',
    muscles: ['Hombros', 'Dorsales', 'Core', 'Oblicuos'],
    equipment: 'Saco de boxeo o pads'
  },
  {
    id: crypto.randomUUID(),
    title: 'Uppercut',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNDlkMnhnYzRvejV5YzRscGtxMGpnOHhidnRzMTN0eHpmeXo0MTdmcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/26ybxccv8Kom5vNUk/giphy.gif',
    category: 'advanced_techniques',
    difficulty: 'intermediate' as const,
    duration_min: 6,
    description: 'Golpe ascendente dirigido hacia arriba',
    technique: 'Flexiona las rodillas y empuja hacia arriba con las piernas',
    muscles: ['Piernas', 'Core', 'Hombros', 'Bíceps'],
    equipment: 'Saco de boxeo o pads'
  },
  {
    id: crypto.randomUUID(),
    title: 'Combinación 1-2',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3YTlodWZ1dnhwbDNicnBvMHB1a2djcjhuenMyNmdkYWI1cGtnajJucyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/S6k8DNjNbUW7EFYYPL/giphy.gif',
    category: 'combinations',
    difficulty: 'intermediate' as const,
    duration_min: 8,
    description: 'Secuencia de jab seguido de cross',
    technique: 'Flujo continuo sin pausas entre golpes',
    muscles: ['Hombros', 'Brazos', 'Core', 'Piernas'],
    equipment: 'Saco de boxeo o pads'
  },
  {
    id: crypto.randomUUID(),
    title: 'Trabajo de Pies',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW82Z216MXdrNzVkODNuMHlqOGtydnJodThlNGN5OTB6NGRwbnJwMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/iKnL9zoFkxEkpuaoXy/giphy.gif',
    category: 'footwork',
    difficulty: 'intermediate' as const,
    duration_min: 12,
    description: 'Movimientos laterales y pivotes',
    technique: 'Mantén la postura de guardia mientras te mueves',
    muscles: ['Piernas', 'Pantorrillas', 'Core', 'Glúteos'],
    equipment: 'Espacio libre'
  },
  {
    id: crypto.randomUUID(),
    title: 'Bloqueos',
    poster_url: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3aWx2aXowcHdsZXpuNHA0bGIyM3ZhaThjdDZyOWhlOHowMTJwbGR3aCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/FHPDgsAJKyp7SraP0Y/giphy.gif',
    category: 'defense',
    difficulty: 'beginner' as const,
    duration_min: 5,
    description: 'Técnicas defensivas con brazos y guantes',
    technique: 'Mantén los codos cerca del cuerpo y guantes arriba',
    muscles: ['Antebrazos', 'Hombros', 'Core'],
    equipment: 'Guantes'
  }
];

// Exercise filters for categorization
const seedFilters = [
  {
    id: crypto.randomUUID(),
    name: 'Fuerza',
    description: 'Ejercicios enfocados en desarrollar fuerza muscular'
  },
  {
    id: crypto.randomUUID(), 
    name: 'Cardio',
    description: 'Ejercicios para mejorar la resistencia cardiovascular'
  },
  {
    id: crypto.randomUUID(),
    name: 'Coordinación',
    description: 'Ejercicios para mejorar la coordinación y técnica'
  },
  {
    id: crypto.randomUUID(),
    name: 'Velocidad',
    description: 'Ejercicios para desarrollar velocidad de golpe'
  },
  {
    id: crypto.randomUUID(),
    name: 'Defensa',
    description: 'Técnicas defensivas y bloqueos'
  }
];

// Initial achievements for gamification
const seedAchievements = [
  {
    id: crypto.randomUUID(),
    user_id: seedUsers[0].id, // Enthusiast user
    name: 'First Steps',
    description: 'Completed your first workout session',
    icon_url: null
  },
  {
    id: crypto.randomUUID(),
    user_id: seedUsers[0].id,
    name: 'Week Warrior', 
    description: 'Trained for 7 consecutive days',
    icon_url: null
  }
];

export async function seedDatabase() {
  try {
    console.log('🌱 Starting mobile database seeding...');
    
    // Check if data already exists
    const existingUsers = await db.select().from(users).limit(1);
    if (existingUsers.length > 0) {
      console.log('✅ Database already seeded, skipping...');
      return;
    }

    // Seed users
    console.log('👤 Seeding users...');
    await db.insert(users).values(seedUsers);
    
    // Seed exercise filters
    console.log('🏷️ Seeding exercise filters...');
    await db.insert(exerciseFilters).values(seedFilters);
    
    // Seed exercises
    console.log('🥊 Seeding exercises...');
    await db.insert(exercises).values(seedExercises);
    
    // Seed achievements
    console.log('🏆 Seeding achievements...');
    await db.insert(achievements).values(seedAchievements);
    
    console.log('✅ Mobile database seeding completed successfully!');
  } catch (error) {
    console.error('❌ Error seeding mobile database:', error);
    throw error;
  }
}