
import { Exercise } from '@/interfaces/interfaces';
import { Image } from 'expo-image';
import { Link } from 'expo-router';
import { Text, TouchableOpacity, View } from 'react-native';

const DIFFICULTY_STYLES = {
    'principiante': 'bg-primary-600/90',
    'intermedio': 'bg-primary-400/90',
    'avanzado': 'bg-primary-300/90',
} as const;

const ExerciseCard = ({ _id, title, posterpath, difficulty, duration }: Exercise) => {
    const difficultyStyle = DIFFICULTY_STYLES[difficulty.toLowerCase() as keyof typeof DIFFICULTY_STYLES]
        || DIFFICULTY_STYLES.principiante;

    return (
        <Link href={`/exercises/${_id}`} asChild>
            <TouchableOpacity
                className="w-[140px] rounded-2xl overflow-hidden bg-gymshock-dark-800"
                activeOpacity={0.85}
                style={{
                    shadowColor: '#B8860B',
                    shadowOffset: { width: 0, height: 6 },
                    shadowOpacity: 0.4,
                    shadowRadius: 12,
                    elevation: 8,
                }}
            >
                <View className='relative'>
                    <Image
                        source={{
                            uri: posterpath || 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png'
                        }}
                        style={{ width: '100%', height: 200 }}
                        className='w-full h-[200px]'
                        autoplay={false}
                    />
                        {/* Subtle dark overlay */}
                    <View className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

                    <View className={`absolute top-3 left-3 px-3 py-1 rounded-full ${difficultyStyle}`}>
                        <Text className="text-white font-oswaldmed text-[10px] uppercase tracking-wider">
                            {difficulty}
                        </Text>
                    </View>
                </View>

                <View className='px-3 py-3'>
                    <Text
                        className='text-sm font-oswaldmed text-white tracking-wide'
                        numberOfLines={1}
                    >
                        {title}
                    </Text>
                    <Text className='text-primary-400 font-spacemono text-xs uppercase mt-1'>
                        {duration}
                    </Text>
                </View>
            </TouchableOpacity>
        </Link>
    )
}

export default ExerciseCard