
import { Exercise } from '@/interfaces/interfaces';
import { Link } from 'expo-router';
import { Image, Text, TouchableOpacity, View } from 'react-native';

const ExerciseCard = ({ _id, title, posterpath, difficulty, duration }: Exercise) => {
    const getBadgeStyle = (type: string, value: string) => {
        const styles = {
            difficulty: {
                'principiante': 'bg-accent-gold-600',
                'intermedio': 'bg-accent-gold-400',
                'avanzado': 'bg-accent-gold-200',
            } as {[key: string]: string},
            duration: 'bg-primary-500/20'
        };

        return type === 'difficulty'
            ? styles.difficulty[value.toLowerCase()] || styles.difficulty.principiante
            : styles.duration;
    };
    return (
        <Link href={`/exercises/${_id}`} asChild>
            <TouchableOpacity
                className="w-[140px] rounded-xl overflow-hidden mx-1"
                activeOpacity={0.9}
                style={{
                    shadowColor: '#000',
                    shadowOffset: { width: 0, height: 4 },
                    shadowOpacity: 0.3,
                    shadowRadius: 8,
                    elevation: 6,
                }}
            >
                <View className='relative'>
                    {/* Image with subtle overlay  */}
                    <View className="relative">
                        <Image
                            source={{
                                uri: posterpath || 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png'
                            }}
                            className='w-full h-52 rounded-xl'
                            resizeMode='cover'
                        />
                        {/* Subtle dark overlay */}
                        <View className="absolute inset-0 bg-black/20 rounded-xl" />
                    </View>

                    <View className={`absolute top-3 left-3 px-3  border backdrop-blur-sm ${getBadgeStyle('difficulty', difficulty)}`}>
                        <Text className="text-white font-oswaldmed text-[10px] uppercase tracking-wide">
                            {difficulty}
                        </Text>
                    </View>
                </View>

                <View className='flex-row items-center justify-start mt-2'>
                    <View className="bg-primary-500/20 px-2 py-1 rounded-full ">
                        <Text
                            className='text-sm font-oswaldmed text-white uppercase tracking-wide'
                            numberOfLines={1}
                        >
                            {title} · <Text className='text-primary-400 font-spacemono text-[10px] uppercase'>{duration}</Text>
                        </Text>
                    </View>
                </View>

            </TouchableOpacity>
        </Link>
    )
}

export default ExerciseCard