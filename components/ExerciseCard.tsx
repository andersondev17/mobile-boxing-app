import { icons } from '@/constants/icons'
import { Exercise } from '@/interfaces/interfaces'
import { Link } from 'expo-router'
import { Image, Text, TouchableOpacity, View } from 'react-native'

const ExerciseCard = ({ _id, title, posterpath, difficulty, duration }: Exercise) => {
    return (
        <Link href={`/exercises/${_id}`} asChild>
            <TouchableOpacity className="w-[100px] rounded-xl overflow-hidden shadow-lg mx-1">
                <View className='relative'>

                    <Image
                        source={{
                            uri: posterpath
                                ? posterpath : 'https://via.placeholder.com/600x400/1a1a1a/ffffff.png'
                        }}
                        className='w-full h-52 rounded-lg'
                        resizeMode='cover'
                    />
                </View>
                <Text className='text-sm font-bold text-white mt-2' numberOfLines={1}>{title}</Text>
                <View className='flex-row items-center justify-start gap-x-1 mt-1'>
                    <Image source={icons.star} className="size-3" />
                    <Text className='text-[10px] text-light-300 font-medium '>{difficulty}</Text>
                </View>
                <View className='flex-row items-center justify-between mt-1'>
                    <Text className='text-[10px] text-light-300 font-medium'>{duration}</Text>
                </View>
            </TouchableOpacity>
        </Link>
    )
}

export default ExerciseCard