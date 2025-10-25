import { Exercise } from '@/interfaces/interfaces';
import { useActionSheet } from '@expo/react-native-action-sheet';
import { Image } from 'expo-image';
import { Link, useRouter } from 'expo-router';
import React from 'react';
import { Share, Text, TouchableOpacity, View } from 'react-native';

const ListCard = ({ exercise }: { exercise: Exercise }) => {
    const { showActionSheetWithOptions } = useActionSheet();
    const router = useRouter();

    const openMenu = () => {
        const options = ['Ver Ejercicio', 'Compartir', 'Cancelar'];
        const cancelButtonIndex = 2;

        showActionSheetWithOptions(
            {
                options,
                cancelButtonIndex,
                title: exercise.title,
                tintColor: '#B8860B',
                containerStyle: {
                    backgroundColor: '#1a1a1f',
                },
                textStyle: {
                    color: '#ffffff',
                    fontFamily: 'Oswald-Medium',
                },
            },
            async (buttonIndex) => {
                if (buttonIndex === 0) {
                    router.push(`/exercises/${exercise._id}`);
                } else if (buttonIndex === 1) {
                    try {
                        await Share.share({
                            message: `¡Mira este ejercicio! ${exercise.title}`,
                            url: `exercises://exercises/${exercise._id}`,
                        });
                    } catch (error) {
                        console.error(error);
                    }
                }
            }
        );
    };

    return (
        <View>
            <View className="flex-row items-center mx-5 py-4">
                <Link href={`/exercises/${exercise._id}`} asChild>
                    <TouchableOpacity className="flex-row items-center flex-1" activeOpacity={0.85}>
                        <View className="relative">
                            <Image
                                source={{ uri: exercise.posterpath }}
                                style={{ width: 80, height: 80, borderRadius: 8 }}
                                autoplay={false}
                            />
                            <View className="absolute inset-0 bg-black/20 rounded-lg" />
                        </View>

                        <View className="ml-4 flex-1">
                            <Text className="text-white font-oswaldmed text-base" numberOfLines={1}>
                                {exercise.title}
                            </Text>
                            <View className="flex-row items-center mt-1 gap-2">
                                <View className="px-2 py-0.5 rounded-full bg-primary-500/20">
                                    <Text className="text-primary-400 text-[10px] font-oswaldmed uppercase">
                                        {exercise.difficulty}
                                    </Text>
                                </View>
                                <Text className="text-light-200 text-xs font-spacemono">
                                    {exercise.duration}
                                </Text>
                            </View>
                        </View>
                    </TouchableOpacity>
                </Link>

                <TouchableOpacity
                    onPress={openMenu}
                    className="w-8 h-8 rounded-full items-center justify-center border border-primary-500/40"
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                    <Text className="text-primary-400 text-xs">⋯</Text>
                </TouchableOpacity>
            </View>
            <View className="h-px bg-primary-500/10 mx-5" />
        </View>
    );
};

export default ListCard