
import { Exercise } from '@/interfaces/interfaces';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
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
                className="w-[140px] h-[250px] rounded-2xl overflow-hidden relative"
                activeOpacity={0.85}
                style={{
                    shadowColor: '#B8860B',
                    shadowOffset: { width: 0, height: 6 },
                    shadowOpacity: 0.4,
                    shadowRadius: 12,
                    elevation: 8,
                }}
            >
                <Image
                    source={{
                        uri: posterpath || 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png'
                    }}
                    style={{ width: '100%', height: '100%' }}
                    contentFit="cover"
                    autoplay={false}
                />

                <LinearGradient
                    colors={['transparent', 'rgba(0,0,0,0.4)', 'rgba(0,0,0,0.95)']}
                    style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
                />

                <View className={`absolute top-3 left-3 px-3 py-1 rounded-full ${difficultyStyle} backdrop-blur-md border border-white/20`}>
                    <Text className="text-white font-oswaldmed text-[10px] uppercase tracking-wider">
                        {difficulty}
                    </Text>
                </View>

                <View className="absolute bottom-3 left-3 right-3">
                    <Text
                        className="text-sm font-oswaldbold text-white tracking-wide mb-1"
                        numberOfLines={1}
                    >
                        {title}
                    </Text>
                    <Text className="text-primary-400 font-spacemono text-[10px] uppercase tracking-widest">
                        {duration}
                    </Text>
                </View>
            </TouchableOpacity>
        </Link>
    )
}

export default ExerciseCard