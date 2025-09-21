import { Exercise } from '@/interfaces/interfaces';
import { Link } from 'expo-router';
import React from 'react';
import { Image, Text, TouchableOpacity, View } from 'react-native';

const ListCard = ({ exercise }: { exercise: Exercise }) => (
    <Link href={`/exercises/${exercise._id}`} asChild>
        <TouchableOpacity className="flex-row items-center mb-4 mx-5">
            <Image
                source={{ uri: exercise.posterpath }}
                className="w-16 h-16 rounded-lg"
                resizeMode="cover"
            />
            <View className="ml-4 flex-1">
                <Text className="text-white font-oswaldmed text-base">
                    {exercise.title}
                </Text>
                <Text className="text-gray-400 text-xs mt-1">
                    {exercise.difficulty} • {exercise.duration}
                </Text>
            </View>
            <View className="w-6 h-6 rounded-full bg-primary-500/20 items-center justify-center">
                <Text className="text-primary-400 text-xs">▶</Text>
            </View>
        </TouchableOpacity>
    </Link>
);

export default ListCard

