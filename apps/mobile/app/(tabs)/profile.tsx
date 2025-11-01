import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import { useRouter } from "expo-router";
import { useCallback } from "react";
import {
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
        className="flex flex-row items-center justify-between py-3"
    >
        <View className="flex flex-row items-center gap-3">
            <Image source={icon} className="size-6" />
            <Text className={`text-base font-spacemono text-white/80 ${textStyle}`}>
                {title}
            </Text>
        </View>

        {showArrow && <Image source={icons.arrow} className="size-5" tintColor="#fff" />}
    </TouchableOpacity>
);

const Profile = () => {
    const handleLogout = async () => { };
    const router = useRouter();

    const handleBack = useCallback(() => router.back(), [router]);

    return (
        <SafeAreaView className="h-full bg-gymshock-dark-900">
            <Image
                source={images.bg}
                className="absolute w-full h-full opacity-25 bg-backgroundImage-premiumGradient"
                resizeMode="cover"
            />

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerClassName="pb-32 px-7"
            >
                <View className="flex flex-row items-center justify-between mt-5">
                    <TouchableOpacity
                        onPress={handleBack}
                        className="w-10 h-10 rounded-full  backdrop-blur-md items-center justify-center"
                        activeOpacity={0.7}
                    >
                        <Image source={icons.back} style={{ width: 20, height: 20 }} tintColor="#fff" />
                    </TouchableOpacity>
                    <Image source={icons.bell} className="size-6" tintColor="#fff" />
                </View>

                <View className="flex flex-row justify-center mt-5">
                    <View className="flex flex-col items-center relative mt-5">
                        <Image
                            source={images.avatar}
                            className="size-44 relative rounded-full"
                        />
                        <TouchableOpacity className="absolute bottom-11 right-2">
                            <Image source={icons.edit} className="size-9" />
                        </TouchableOpacity>

                        <Text className="text-2xl font-oswaldbold text-white mt-2">John Doe</Text>
                        <Text className="text-xs font-spacemono text-white/60 uppercase tracking-widest mt-1">
                            Miembro Premium
                        </Text>
                    </View>
                </View>

                <View className="flex flex-col mt-10 bg-gymshock-dark-800/95  rounded-3xl p-5 border border-white/5">
                    <SettingsItem icon={icons.play} title="Mis Entrenamientos" />
                    <SettingsItem icon={icons.search} title="Guardados" />
                </View>

                <View className="flex flex-col mt-5 bg-gymshock-dark-800/95  rounded-3xl p-5 border border-white/5 shadow-lg shadow-black">
                    <SettingsItem icon={icons.bell} title="Notificaciones" />
                    <SettingsItem icon={icons.person} title="Privacidad" />
                    <SettingsItem icon={icons.search} title="Configuración" />
                </View>

                <View className="flex flex-col mt-5 bg-gymshock-dark-800/95  rounded-3xl p-5 border border-white/5">
                    <SettingsItem
                        icon={icons.logout}
                        title="Cerrar Sesión"
                        textStyle="text-red-500"
                        showArrow={false}
                        onPress={handleLogout}
                    />
                </View>
            </ScrollView>
        </SafeAreaView>
    );
};

export default Profile;