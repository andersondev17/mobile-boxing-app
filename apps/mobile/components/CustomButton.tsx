// CustomButton.tsx
import { CustomButtonProps } from "@/types/type";
import cn from "clsx";
import React from 'react';
import { ActivityIndicator, Text, TouchableOpacity, View } from 'react-native';

const CustomButton = ({
    onPress,
    title = "Click Me",
    style,
    textStyle,
    leftIcon,
    isLoading = false
}: CustomButtonProps) => {
    return (
        <TouchableOpacity 
            className={cn('bg-primary-500 py-4 rounded-full items-center justify-center', style)} 
            onPress={onPress}
            activeOpacity={0.85}
            disabled={isLoading}
        >
            {leftIcon}

            <View className="flex-center flex-row">
                {isLoading ? (
                    <ActivityIndicator size="small" color="white" />
                ) : (
                    <Text className={cn('text-white font-oswaldbold text-base uppercase tracking-wide', textStyle)}>
                        {title}
                    </Text>
                )}
            </View>
        </TouchableOpacity>
    )
}
export default CustomButton