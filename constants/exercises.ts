export const BOXING_EXERCISES = [
    {
        _id: 1,
        title: 'Jab',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3c2dhcDM2dmIxNGhjcXBidGQ0cTRwdDhvNHR2NHFqcjA2anJpd2R6cyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ovzh1nMQQMOMXE3WVx/giphy.gif',
        category: 'Golpes Básicos',
        difficulty: 'Principiante',
        duration: '3-5 min',
        description: 'Golpe directo con la mano adelantada',
        technique: 'Extiende el brazo adelantado en línea recta hacia el objetivo',
        muscles: ['Hombros', 'Tríceps', 'Core'],
        equipment: 'Saco de boxeo o pads'
    },
    {
        _id: 2,
        title: 'Cross',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3NTRpYmllb2YwZGphNXowZGl6YzR2ZHF0aHZnM2NzMmR1ZmNoanprcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUySTxL9fZyjIKzoLS/giphy.gif',
        category: 'Golpes Básicos',
        difficulty: 'Principiante',
        duration: '3-5 min',
        description: 'Golpe directo con la mano trasera',
        technique: 'Rota la cadera y pivotea el pie trasero al lanzar',
        muscles: ['Hombros', 'Espalda', 'Core', 'Piernas'],
        equipment: 'Saco de boxeo o pads'
    },
    {
        _id: 3,
        title: 'Hook',
        category: 'Golpes de Gancho',
        posterpath:'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZHM3Y3QzNjNoZGU4Z2dycHN0cTdia2Nzd3RnZXA0bzFuOWlvbDBxYSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/lmHf50zYQPAYmHvTGR/giphy.gif',
        difficulty: 'Intermedio',
        duration: '4-6 min',
        description: 'Golpe circular dirigido al costado del objetivo',
        technique: 'Mantén el codo alto y rota desde la cadera',
        muscles: ['Hombros', 'Dorsales', 'Core', 'Oblicuos'],
        equipment: 'Saco de boxeo o pads'
    },
    {
        _id: 4,
        title: 'Uppercut',
        category: 'Golpes Ascendentes',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNDlkMnhnYzRvejV5YzRscGtxMGpnOHhidnRzMTN0eHpmeXo0MTdmcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/26ybxccv8Kom5vNUk/giphy.gif',

        difficulty: 'Intermedio',
        duration: '4-6 min',
        description: 'Golpe ascendente dirigido hacia arriba',
        technique: 'Flexiona las rodillas y empuja hacia arriba con las piernas',
        muscles: ['Piernas', 'Core', 'Hombros', 'Bíceps'],
        equipment: 'Saco de boxeo o pads'
    },
    {
        _id: 5,
        title: 'Combinación 1-2',
        category: 'Combinaciones',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3YTlodWZ1dnhwbDNicnBvMHB1a2djcjhuenMyNmdkYWI1cGtnajJucyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/S6k8DNjNbUW7EFYYPL/giphy.gif',

        difficulty: 'Intermedio',
        duration: '5-8 min',
        description: 'Secuencia de jab seguido de cross',
        technique: 'Flujo continuo sin pausas entre golpes',
        muscles: ['Hombros', 'Brazos', 'Core', 'Piernas'],
        equipment: 'Saco de boxeo o pads'
    },
    {
        _id: 6,
        title: 'Esquiva y Contra',
        category: 'Defensa Activa',
        posterpath: 'https://via.placeholder.com/150',

        difficulty: 'Avanzado',
        duration: '6-10 min',
        description: 'Movimiento defensivo seguido de contraataque',
        technique: 'Flexiona rodillas para esquivar, luego contraataca inmediatamente',
        muscles: ['Piernas', 'Core', 'Brazos', 'Glúteos'],
        equipment: 'Pads o sparring'
    },
    {
        _id: 7,
        title: 'Trabajo de Pies',
        category: 'Movilidad',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW82Z216MXdrNzVkODNuMHlqOGtydnJodThlNGN5OTB6NGRwbnJwMSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/iKnL9zoFkxEkpuaoXy/giphy.gif',

        difficulty: 'Intermedio',
        duration: '8-12 min',
        description: 'Movimientos laterales y pivotes',
        technique: 'Mantén la postura de guardia mientras te mueves',
        muscles: ['Piernas', 'Pantorrillas', 'Core', 'Glúteos'],
        equipment: 'Espacio libre'
    },
    {
        _id: 8,
        title: 'Bloqueos',
        category: 'Defensa',
        posterpath: 'https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3aWx2aXowcHdsZXpuNHA0bGIyM3ZhaThjdDZyOWhlOHowMTJwbGR3aCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/FHPDgsAJKyp7SraP0Y/giphy.gif',
        difficulty: 'Principiante',
        duration: '3-5 min',
        description: 'Técnicas defensivas con brazos y guantes',
        technique: 'Mantén los codos cerca del cuerpo y guantes arriba',
        muscles: ['Antebrazos', 'Hombros', 'Core'],
        equipment: 'Guantes'
    },
    {
        _id: 9,
        title: 'Slip y Roll',
        category: 'Defensa Activa',
        posterpath: 'https://via.placeholder.com/150',

        difficulty: 'Avanzado',
        duration: '6-8 min',
        description: 'Movimientos evasivos para evitar golpes',
        technique: 'Mueve la cabeza fuera de la línea de ataque',
        muscles: ['Cuello', 'Core', 'Piernas', 'Espalda baja'],
        equipment: 'Pads o sparring'
    }
];

export type Exercise = typeof BOXING_EXERCISES[0];

// Mock function para simular llamada al backend
export const fetchExercises = async ({ query }: { query: string }): Promise<Exercise[]> => {
    // Simula latencia de red
    await new Promise(resolve => setTimeout(resolve, 800));

    // Simula filtrado por query si existe
    if (query.trim()) {
        return BOXING_EXERCISES.filter(exercise =>
            exercise.title.toLowerCase().includes(query.toLowerCase()) ||
            exercise.category.toLowerCase().includes(query.toLowerCase())
        );
    }

    return BOXING_EXERCISES;
};