import CustomButton from "@/components/CustomButton";
import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import { useAuthStore, useUser } from "@/store/authStore";
import { useRouter } from "expo-router";
import { useCallback } from "react";
import {
    Alert,
    Image,
    ImageSourcePropType,
    SafeAreaView,
    ScrollView,
    Text,
    TouchableOpacity,
    View
} from "react-native";

interface SettingsItemProp {
    icon: ImageSourcePropType;
    title: string;
    onPress?: () => void;
    textStyle?: string;
    showArrow?: boolean;
}

const SettingsItem = ({
    icon,
    title,
    onPress,
    textStyle,
    showArrow = true,
}: SettingsItemProp) => (
    <TouchableOpacity
        onPress={onPress}
        className="flex-row items-center justify-between py-2 border-b border-white/5 last:border-0"
        activeOpacity={0.7}
    >
        <View className="flex-row items-center gap-3">
            <View className="w-10 h-10 bg-white/5 rounded-xl items-center justify-center">
                <Image source={icon} className="size-4" tintColor="#fff" />
            </View>
            <Text className={`text-base font-spacemono ${textStyle || 'text-white/80'}`}>
                {title}
            </Text>
        </View>

        {showArrow && (
            <Image source={icons.back}    style={{ transform: [{ rotate: '180deg' }] }} className="size-3 opacity-40" tintColor="#fff" />
        )}
    </TouchableOpacity>
);

const Profile = () => {
    const user = useUser();
    const { signOut, isLoading } = useAuthStore();
    const router = useRouter();

    const handleBack = useCallback(() => router.back(), [router]);

    const handleLogout = async () => {
        Alert.alert(
            'Cerrar Sesión',
            '¿Estás seguro que deseas cerrar sesión?',
            [
                {
                    text: 'Cancelar',
                    style: 'cancel',
                },
                {
                    text: 'Cerrar Sesión',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await signOut();
                            router.replace('/sign-in');
                        } catch (error: any) {
                            Alert.alert('Error', 'No se pudo cerrar sesión');
                        }
                    },
                },
            ]
        );
    };

    return (
        <SafeAreaView className="flex-1 bg-gymshock-dark-900">
            <Image
                source={images.bg}
                className="absolute w-full h-full opacity-25"
                resizeMode="cover"
            />

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={{ paddingBottom: 120 }}
                className="px-6"
            >
                <View className="flex-row items-center justify-between mt-6 mb-8">
                    <TouchableOpacity
                        onPress={handleBack}
                        className="w-11 h-11  items-center justify-center"
                        activeOpacity={0.7}
                    >
                        <Image source={icons.back} className="size-5" tintColor="#fff" />
                    </TouchableOpacity>

                    <TouchableOpacity
                        className="w-11 h-11  items-center justify-center"
                        activeOpacity={0.7}
                    >
                        <Image source={icons.bell} className="size-5" tintColor="#fff" />
                    </TouchableOpacity>
                </View>

                {/* Profile Section */}
                <View className="items-center mb-8">
                    <View className="relative">
                        {user?.picture ? (
                            <Image
                                source={{ uri: user.picture }}
                                className="size-32 rounded-full border-4 border-white/10"
                            />
                        ) : (
                            <Image
                                source={images.avatar}
                                className="size-32 rounded-full border-4 border-white/10"
                            />
                        )}
                        <TouchableOpacity
                            className="absolute -bottom-2 -right-2 w-10 h-10 bg-primary-400 rounded-full items-center justify-center shadow-lg shadow-black/50"
                            activeOpacity={0.8}
                        >
                            <Image source={icons.edit} className="size-5" tintColor="#1a1a1a" />
                        </TouchableOpacity>
                    </View>

                    <Text className="text-3xl font-oswaldbold text-white mt-4">
                        {user?.name || 'Usuario'}
                    </Text>
                    <Text className="text-xs font-spacemono text-white/50 uppercase tracking-widest mt-1">
                        {user?.email || 'No autenticado'}
                    </Text>
                    {user?.provider && (
                        <View className="flex-row items-center mt-2 bg-white/10 px-3 py-1 rounded-full">
                            <Text className="text-xs font-spacemono text-primary-400 uppercase tracking-wider">
                                {user.provider === 'google' ? '🔗 Google' : '📧 Email'}
                            </Text>
                        </View>
                    )}
                </View>

                <Text className="text-white/50 text-sm font-spacemono uppercase tracking-widest mb-2 pl-4">
                    Actividad
                </Text>
                <View className="bg-gymshock-dark-800/95 rounded-2xl p-2 border border-white/5 mb-4 shadow-lg shadow-black/50">
                    <SettingsItem icon={icons.play} title="Mis Entrenamientos" />
                    <SettingsItem icon={icons.search} title="Guardados" />
                </View>

                <Text className="text-white/50 text-sm font-spacemono uppercase tracking-widest mb-2 pl-4">
                    Ajustes
                </Text>
                <View className="bg-gymshock-dark-800/95 rounded-2xl p-2 border border-white/5 mb-4 shadow-lg shadow-black/50">
                    <SettingsItem icon={icons.bell} title="Notificaciones" />
                    <SettingsItem icon={icons.person} title="Privacidad" />
                    <SettingsItem icon={icons.search} title="Ajustes" />
                </View>

                <CustomButton
                    title="CERRAR SESIÓN"
                    onPress={handleLogout}
                    variant="primary"
                    isLoading={isLoading}
                    leftIcon={<Image source={icons.logout} className="size-5" tintColor="#1a1a1a" />}
                />
            </ScrollView>
        </SafeAreaView>
    );
};

export default Profile;
