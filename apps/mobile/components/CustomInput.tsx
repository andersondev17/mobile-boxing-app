// CustomInput.tsx
import { CustomInputProps } from "@/types/type";
import cn from "clsx";
import { useState } from "react";
import { Text, TextInput, TouchableOpacity, View } from 'react-native';

const CustomInput = ({
    placeholder = 'Enter text',
    value,
    onChangeText,
    label,
    secureTextEntry = false,
    keyboardType = "default",
    error = false,
    errorMessage
}: CustomInputProps) => {
    const [isFocused, setIsFocused] = useState(false);
    const [isPasswordVisible, setIsPasswordVisible] = useState(false);

    const shouldShowPassword = secureTextEntry && !isPasswordVisible;

    return (
        <View className="w-full">
            <Text className="text-white/60 font-spacemono text-xs uppercase tracking-widest mb-2">
                {label}
            </Text>

            <View className="relative">
                <TextInput
                    autoCapitalize="none"
                    autoCorrect={false}
                    value={value}
                    onChangeText={onChangeText}
                    secureTextEntry={shouldShowPassword}
                    keyboardType={keyboardType}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder={placeholder}
                    placeholderTextColor="#666"
                    className={cn(
                        'bg-white/5 text-white font-spacemono text-sm px-4 py-4 rounded-xl border',
                        error ? 'border-red-500' : isFocused ? 'border-primary-400' : 'border-white/10'
                    )}
                />

                {secureTextEntry && (
                    <TouchableOpacity
                        onPress={() => setIsPasswordVisible(!isPasswordVisible)}
                        className="absolute right-4 top-4"
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                        <Text className="text-white/60 font-spacemono text-xs">
                            {isPasswordVisible ? '🙈' : '👁️'}
                        </Text>
                    </TouchableOpacity>
                )}
            </View>

            {error && errorMessage && (
                <Text className="text-red-400 font-spacemono text-xs mt-1">
                    {errorMessage}
                </Text>
            )}
        </View>
    )
}
export default CustomInput;