import { icons } from '@/constants/icons';
import { images } from '@/constants/images';
import { Dimensions, Image, ImageBackground, KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native';

interface AuthContainerProps {
    children: React.ReactNode;
}

export default function AuthContainer({ children }: AuthContainerProps) {
    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            className="flex-1"
        >
            <ScrollView
                className="bg-gymshock-dark-900"
                keyboardShouldPersistTaps="handled"
                contentContainerStyle={{ flexGrow: 1 }}
                showsVerticalScrollIndicator={false}
            >
                <Image
                    source={images.bg}
                    className="absolute w-full h-full opacity-25"
                    resizeMode="cover"
                />

                <View className="w-full relative items-center" style={{ height: Dimensions.get('screen').height * 0.30 }}>
                    <ImageBackground
                        source={images.gloves}
                        className="absolute w-full h-full rounded-b-2xl opacity-90"
                        resizeMode="cover"
                    />

                    <View className="absolute -bottom-20 z-20">
                        <Image
                            source={icons.logo}
                            className="size-40 rounded-full shadow-2xl shadow-black/80"
                            resizeMode="contain"
                        />
                    </View>
                </View>

                <View className="pt-24">
                    {children}
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}
