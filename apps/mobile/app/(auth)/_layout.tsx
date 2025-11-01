import { icons } from '@/constants/icons';
import { images } from '@/constants/images';
import { Slot } from "expo-router";
import { Dimensions, Image, ImageBackground, KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native';
/* import useAuthStore from "@/store/auth.store";
 */
export default function AuthLayout() {
    /*     const { isAuthenticated } = useAuthStore();
    
        if(isAuthenticated) return <Redirect href="/" />
     */
    return (
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <ScrollView className="bg-gymshock-dark-900 h-full" keyboardShouldPersistTaps="handled">
                <Image
                    source={images.bg}
                    className="absolute w-full h-full opacity-25 bg-backgroundImage-premiumGradient"
                    resizeMode="cover"
                />

                <View className="w-full relative" style={{ height: Dimensions.get('screen').height / 2.25 }}>
                    <ImageBackground source={images.gloves} className="size-full rounded-b-lg" resizeMode="stretch" />
                    <Image source={icons.logo} className="self-center size-48 absolute -bottom-16 z-10 rounded-full" />
                </View> 
                <Slot />
            </ScrollView>
        </KeyboardAvoidingView>
    )
}