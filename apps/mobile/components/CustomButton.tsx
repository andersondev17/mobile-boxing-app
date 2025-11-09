// CustomButton.tsx
import { images } from "@/constants/images";
import { CustomButtonProps } from "@/types/type";
import cn from "clsx";
import React from 'react';
import { ActivityIndicator, ImageBackground, Text, TouchableOpacity, View, ViewStyle } from 'react-native';

const LOADER_COLORS = {
    primary: "#1a1a1a",
    default: "#ffffff",
} as const;

const CustomButton = ({
    onPress,
    title = "Click Me",
    style,
    textStyle,
    leftIcon,
    rightIcon,
    isLoading = false,
    disabled = false,
    variant = "default"
}: CustomButtonProps) => {
    const isPrimary = variant === "primary";
    const isDisabled = isLoading || disabled;

    const buttonContent = (
        <>
            {leftIcon && <View className="mr-2">{leftIcon}</View>}
            {isLoading ? (
                <ActivityIndicator
                    size="small"
                    color={LOADER_COLORS[variant]}
                />
            ) : (
                <Text
                    className={cn(
                        'font-spacemono font-bold text-base tracking-widest',
                        isPrimary ? 'text-gymshock-dark-900' : 'text-white',
                        textStyle
                    )}
                >
                    {title}
                </Text>
            )}
            {rightIcon && <View className="ml-2">{rightIcon}</View>}
        </>
    );

    const opacityStyle: ViewStyle = { opacity: isDisabled ? 0.4 : 1 };

    const sharedProps = {
        onPress,
        activeOpacity: 0.85,
        disabled: isDisabled,
        accessibilityRole: "button" as const,
        accessibilityLabel: title,
        accessibilityState: { disabled: isDisabled, busy: isLoading },
    };

    if (isPrimary) {
        return (
            <TouchableOpacity 
                {...sharedProps}
                className={cn('rounded-full overflow-hidden', style)}
                style={opacityStyle}
            >
                <ImageBackground
                    source={images.goldHighlight}
                    className="py-4"
                    resizeMode="cover"
                >
                    <View className="flex-row items-center justify-center">
                        {buttonContent}
                    </View>
                </ImageBackground>
            </TouchableOpacity>
        );
    }

    return (
        <TouchableOpacity 
            {...sharedProps}
            className={cn('bg-primary-500 py-4 rounded-full', style)}
            style={opacityStyle}
        >
            <View className="flex-row items-center justify-center">
                {buttonContent}
            </View>
        </TouchableOpacity>
    )
}
export default CustomButton;