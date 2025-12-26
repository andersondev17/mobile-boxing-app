import ListCard from '@/components/ListCard';
import { icons } from '@/constants/icons';
import { images } from '@/constants/images';
import { useSavedExercises } from '@/hooks/useSavedExercises';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'expo-router';

import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Animated, FlatList, Image, RefreshControl, StatusBar, Text, TouchableOpacity, View } from 'react-native';

const EmptyState = () => (
    <View className="flex-1 justify-center items-center px-8 py-20">
        <View className="w-24 h-24 rounded-full bg-primary-500/10 items-center justify-center mb-6">
            <Image
                source={icons.agregar}
                style={{ width: 40, height: 40 }}
                tintColor="#C29B2E"
            />
        </View>
        <Text className="text-white font-oswaldbold text-2xl mb-3 text-center">
            Aun no tienes técnicas Guardadas
        </Text>
        <Text className="text-white/60 font-spacemono text-sm text-center leading-6">
            Guarda tus técnicas para poder usarlas en tus ejercicios
        </Text>
    </View>
);
const AuthRequiredState = ({ router }: { router: any }) => (
    <View className="flex-1 justify-center items-center px-8 py-20">
        <View className="w-32 h-32 rounded-full bg-gradient-to-br from-primary-500/10 to-primary-600/5 items-center justify-center mb-8 border border-primary-500/20">
            <Image
                source={icons.agregar}
                style={{ width: 48, height: 48 }}
                tintColor="#C29B2E"
            />
        </View>
        <Text className="text-white font-oswaldbold text-2xl mb-4 text-center">
            Inicia sesión para guardar
        </Text>
        <Text className="text-white/60 font-spacemono text-sm text-center leading-6 px-12 mb-8">
            Inicia sesión para guardar ejercicios y crear tu colección personal
        </Text>
        <TouchableOpacity
            className="bg-primary-500 px-8 py-3 rounded-full"
            onPress={() => router.push('/(auth)/sign-in')}
        >
            <Text className="text-white font-oswaldmed text-base">Iniciar sesión</Text>
        </TouchableOpacity>
    </View>
);

const Saved = () => {
    const router = useRouter();
    const { savedExercises, loading, refresh } = useSavedExercises();
    const { isAuthenticated } = useAuthStore();
    const [refreshing, setRefreshing] = useState(false);
    const [scrollY] = useState(new Animated.Value(0));

    const headerHeight = scrollY.interpolate({
        inputRange: [0, 100],
        outputRange: [100, 70],
        extrapolate: 'clamp',
    });

    const headerOpacity = scrollY.interpolate({
        inputRange: [0, 50],
        outputRange: [1, 0.9],
        extrapolate: 'clamp',
    });
    const headerBg = scrollY.interpolate({
        inputRange: [0, 100],
        outputRange: ['rgba(10, 10, 15, 0)', 'rgba(10, 10, 15, 0.95)'],
        extrapolate: 'clamp',
    });
    const onRefresh = useCallback(async () => {
        setRefreshing(true);
        await refresh();
        setRefreshing(false);
    }, [refresh]);

    if (!isAuthenticated) {
        return (
            <View className="flex-1 bg-gymshock-dark-900">
                <Image
                    source={images.bg}
                    className="absolute w-full h-full opacity-25 bg-backgroundImage-premiumGradient"
                    resizeMode="cover"
                />
                <View className="px-5  flex-row items-center justify-between">
                    <TouchableOpacity
                        onPress={() => router.back()}
                        className="w-10 h-10 rounded-full bg-white/5 items-center justify-center border border-white/10"
                        activeOpacity={0.85}
                    >
                        <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
                    </TouchableOpacity>
                    <Text className="text-white font-oswaldbold text-xl">Técnicas Guardadas</Text>
                    <View className="w-10" />
                </View>
                <AuthRequiredState router={router} />
            </View>
        );
    }

    return (
        <View className="flex-1 bg-gymshock-dark-900">
            <Image
                source={images.bg}
                className="absolute w-full h-full opacity-25"
                resizeMode="cover"
            />

            <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />

            {loading && !refreshing ? (
                <View className="flex-1 justify-center items-center">
                    <ActivityIndicator size="large" color="#C29B2E" />
                    <Text className="text-white/60 mt-4 font-spacemono">Cargando tu biblioteca...</Text>
                </View>

            ) : (

                <FlatList
                    data={savedExercises}
                    keyExtractor={(item, index) => item._id || `exercise-${index}`}
                    renderItem={({ item }) => <ListCard exercise={item} />}
                    ListEmptyComponent={<EmptyState />}
                    contentContainerStyle={{
                        flexGrow: 1,
                        paddingTop: 120,
                        paddingBottom: 120, // Espacio para el bottom tab
                    }}
                    refreshControl={
                        <RefreshControl
                            refreshing={refreshing}
                            onRefresh={onRefresh}
                            tintColor="#C29B2E"
                            colors={['#C29B2E']}
                            title="Actualizando..."
                            titleColor="#C29B2E"
                        />
                    }
                    showsVerticalScrollIndicator={false}
                    onScroll={Animated.event(
                        [{ nativeEvent: { contentOffset: { y: scrollY } } }],
                        { useNativeDriver: false }
                    )}
                    scrollEventThrottle={16}
                    initialNumToRender={8}
                    maxToRenderPerBatch={8}
                    windowSize={5}
                    removeClippedSubviews={true}
                    ListHeaderComponent={
                        savedExercises.length > 0 ? (
                            <View className="px-4 py-4">
                                <Text className="text-white font-oswaldbold text-2xl mb-2">Tu colección</Text>

                                {/* Contador */}
                                {!loading && savedExercises.length > 0 && (
                                    <Text className="text-white/60 font-spacemono text-sm pb-2">
                                        {savedExercises.length} {savedExercises.length === 1 ? 'ejercicio' : 'ejercicios'}
                                    </Text>
                                )}
                            </View>
                        ) : null
                    }
                />
            )}
              <Animated.View
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: headerHeight,
                    backgroundColor: headerBg,
                }}
                className="px-5 pt-14 pb-3 flex-row items-end justify-between border-b border-white/5"
            >
                <TouchableOpacity
                    onPress={() => router.back()}
                    className="w-10 h-10 items-center justify-center  mb-2"
                    activeOpacity={0.85}
                >
                    <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
                </TouchableOpacity>
            </Animated.View>
        </View>
    );
};

export default Saved;