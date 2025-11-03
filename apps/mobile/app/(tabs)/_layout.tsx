import { icons } from '@/constants/icons';
import { BlurView } from 'expo-blur';
import * as Haptics from 'expo-haptics';
import { Redirect, Tabs } from 'expo-router';
import React, { useEffect, useRef } from 'react';
import {
    Animated,
    Dimensions,
    Image,
    Text,
    TouchableOpacity,
    View
} from "react-native";
import Svg, { Ellipse } from 'react-native-svg';

const { width: screenWidth } = Dimensions.get('window');
const TAB_HEIGHT = 38;
const BRAND_LAYER_HEIGHT = 60;
const TABS_COUNT = 4;
const TAB_WIDTH = screenWidth / TABS_COUNT;

const TabIcon = ({ focused, icon }: any) => {
    const underlineWidth = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        Animated.timing(underlineWidth, {
            toValue: focused ? 20 : 0,
            duration: 250,
            useNativeDriver: false,
        }).start();
    }, [focused]);
    if (focused) {
        Haptics.selectionAsync();
    }
    return (

        <View className="flex-1 items-center justify-center h-full">
            <View className="items-center">
                <Image
                    source={icon}
                    tintColor={focused ? "#B8860B" : "#888888"}
                    className="size-6 mb-1"
                />
                {/* Línea debajo cuando está activo */}
                {focused && (

                    <Animated.View
                        style={{
                            height: 3,
                            width: underlineWidth,
                            backgroundColor: "#B8860B",
                            borderRadius: 2,
                            marginTop: 2,
                        }}
                    />
                )}
            </View>
        </View>
    );
};


const CurvedTabBar = ({ state, descriptors, navigation }: any) => {
    const animatedValue = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        Animated.spring(animatedValue, {
            toValue: state.index,
            useNativeDriver: false,
            tension: 200,
            friction: 10,
        }).start();
    }, [state.index]);

    return (
        <View  className="absolute bottom-0 left-0 right-0  shadow-2xl shadow-black/30">
            {/* Contenedor principal con fondo para tapar espacios */}
            <BlurView  intensity={80} tint="dark" className='rounded-t-2xl overflow-hidden'>
                {/* Navigation Area */}
                <View style={{ height: TAB_HEIGHT }}>
                    <View className="flex-row h-full">
                        {state.routes.map((route: any, index: number) => {
                            const isFocused = state.index === index;

                            const onPress = () => {
                                const event = navigation.emit({
                                    type: 'tabPress',
                                    target: route.key,
                                    canPreventDefault: true,
                                });

                                if (!isFocused && !event.defaultPrevented) {
                                    navigation.navigate(route.name);
                                }
                            };

                            return (
                                <TouchableOpacity
                                    key={route.key}
                                    onPress={onPress}
                                    style={{ width: TAB_WIDTH }}
                                    className="h-full"
                                    activeOpacity={0.8}
                                >
                                    <TabIcon
                                        focused={isFocused}
                                        icon={getIconForRoute(route.name)}
                                    />
                                </TouchableOpacity>
                            );
                        })}
                    </View>
                </View>

                <View style={{ position: "relative", marginTop: -20 }}>
                    <Svg
                        width={screenWidth}
                        height={BRAND_LAYER_HEIGHT}
                        style={{ position: "absolute", bottom: 0 }}
                    >
                        {/* Brand layer ellipse - Ajustado para cubrir todo el ancho */}
                        <Ellipse
                            cx={screenWidth / 2}
                            cy={BRAND_LAYER_HEIGHT - 15}
                            rx={screenWidth / 2}  // Cambiado para cubrir todo el ancho
                            ry={25}
                            fill="#1A1A1A"
                            stroke="rgba(184, 134, 11, 0.2)"
                            strokeWidth={1}
                        />
                    </Svg>

                    <View
                        style={{
                            height: BRAND_LAYER_HEIGHT,
                            justifyContent: 'center',
                            alignItems: 'center'
                        }}
                    >
                        <Text className="text-primary-500 font-oswaldmed text-sm tracking-[2px] ">
                            {getTitleForRoute(state.routes[state.index].name)}
                        </Text>
                    </View>
                </View>
            </BlurView>
        </View>
    );
};

// Helper functions
const getIconForRoute = (routeName: string): any => {
    const iconMap: Record<string, any> = {
        index: icons.home,
        saved: icons.save,
        search: icons.search,
        profile: icons.person,
    };
    return iconMap[routeName] || icons.home;
};

const getTitleForRoute = (routeName: string): string => {
    const titleMap: Record<string, string> = {
        index: "Inicio",
        saved: "Favoritos",
        search: "Buscar",
        profile: "Perfil",
    };
    return titleMap[routeName] || "Tab";
};

const _layout = () => {
    const isAuthenticated = true; //TODO: replace with actual auth logic
    if(!isAuthenticated) return <Redirect href="/sign-in" />

    return (
        <Tabs
            tabBar={(props) => <CurvedTabBar {...props} />}
            screenOptions={{
                headerShown: false,
            }}
        >
            <Tabs.Screen name="index" />
            <Tabs.Screen name="saved" />
            <Tabs.Screen name="search" />
            <Tabs.Screen name="profile" />
        </Tabs>
    );
};

export default _layout;