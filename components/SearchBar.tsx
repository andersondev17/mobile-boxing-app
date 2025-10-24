// SearchBar.tsx
import { icons } from '@/constants/icons'
import React from 'react'
import { Image, Pressable, Text, TextInput, TouchableOpacity, View } from 'react-native'

interface Props {
    placeholder: string
    onPress?: () => void
    value?: string
    onChangeText?: (text: string) => void
    autoFocus?: boolean
    showCancel?: boolean
    onCancel?: () => void
}

const SearchBar = ({ placeholder, onPress, value, onChangeText, autoFocus, showCancel, onCancel }: Props) => {
    const handleClear = () => {
        onChangeText?.('')
    }

    return (
        <View className='flex-row items-center gap-3'>
            <View className='flex-1 flex-row items-center bg-dark-200 rounded-full px-5 py-2 shadow-lg border border-gray-800'>
                {onPress ? (
                    <Pressable onPress={onPress} className='flex-1'>
                        <Text className='text-[#a8b5db] font-spacemono'>
                            {placeholder}
                        </Text>
                    </Pressable>
                ) : (
                    <TextInput
                        autoFocus={autoFocus}
                        placeholder={placeholder}
                        value={value}
                        onChangeText={onChangeText}
                        placeholderTextColor="#a8b5db"
                        className='flex-1 text-white font-spacemono text-base'
                    />
                )}

                {value && value.length > 0 && (
                    <TouchableOpacity
                        onPress={handleClear}
                        className='ml-2 p-1'
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                        <Image
                            source={icons.close}
                            className="w-3 h-4"
                            tintColor="#a8b5db"
                        />
                    </TouchableOpacity>
                )}
            </View>

            {showCancel && (
                <TouchableOpacity onPress={onCancel}>
                    <Text className='text-white font-spacemono text-sm'>
                        Cancelar
                    </Text>
                </TouchableOpacity>
            )}
        </View>
    )
}

export default SearchBar