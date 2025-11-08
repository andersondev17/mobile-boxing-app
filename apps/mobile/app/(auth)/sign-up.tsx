// sign-up.tsx
import CustomButton from "@/components/CustomButton";
import CustomInput from "@/components/CustomInput";
import { useAuthStore } from '@/store/authStore';
import { Link, router } from "expo-router";
import { useState } from "react";
import { Alert, Text, TouchableOpacity, View } from 'react-native';

const SignUp = () => {
    const { signUp, isLoading, clearError } = useAuthStore();
    const [form, setForm] = useState({ name: '', email: '', password: '' });
    const [termsAccepted, setTermsAccepted] = useState(false);

    const isFormValid = form.name.trim() && form.email.trim() && form.password.trim() && termsAccepted;

    const handleSignUp = async () => {
        clearError();
        try {
            await signUp({ name: form.name, email: form.email, password: form.password });
            Alert.alert(
                'Cuenta creada',
                'Tu cuenta ha sido creada exitosamente. Ahora puedes iniciar sesión.',
                [{ text: 'Iniciar Sesión', onPress: () => router.push('/sign-in') }]
            );
        } catch (error: any) {
            const errorMessage = error?.detail || error?.message || 'Error al crear cuenta';
            Alert.alert('Error', errorMessage);
        }
    }

    return (
        <View className="px-6 pt-8 pb-12">
            <View className="mb-8">

                <Text className="text-white text-4xl font-oswaldbold text-center mb-2">
                    Crea tu cuenta
                </Text>
                <Text className="text-white/60 text-xs font-spacemono  tracking-wider mb-2 text-center">
                    BIENVENIDO A GYMSHOCK
                </Text>
            </View>


            {/* Form */}
            <View className="gap-4 mb-6">
                <CustomInput
                    placeholder="Ingrese su nombre completo"
                    value={form.name}
                    onChangeText={(text) => setForm((prev) => ({ ...prev, name: text }))}
                    label="Nombre completo"
                />
                <CustomInput
                    placeholder="Ingrese su email"
                    value={form.email}
                    onChangeText={(text) => setForm((prev) => ({ ...prev, email: text }))}
                    label="Email"
                    keyboardType="email-address"
                />
                <CustomInput
                    placeholder="Ingrese su contraseña"
                    value={form.password}
                    onChangeText={(text) => setForm((prev) => ({ ...prev, password: text }))}
                    label="Contraseña"
                    secureTextEntry
                />
            </View>

            {/* Terms Checkbox */}
            <View className="flex-row items-start gap-3 mb-6">
                <TouchableOpacity
                    onPress={() => setTermsAccepted(!termsAccepted)}
                    className={`w-5 h-5 mt-1 rounded border-2 items-center justify-center ${
                        termsAccepted ? 'bg-primary-400 border-primary-400' : 'border-white/40'
                    }`}
                >
                    {termsAccepted && <Text className="text-gymshock-dark-900 text-xs font-bold">✓</Text>}
                </TouchableOpacity>

                <View className="flex-1">
                    <Text className="text-white/80 text-xs font-spacemono leading-5">
                        Acepto los{' '}
                        <Text
                            onPress={() => router.push('/(auth)/terms')}
                            className="text-primary-400 underline"
                        >
                            Términos y Condiciones
                        </Text>
                        {' '}y la{' '}
                        <Text
                            onPress={() => router.push('/(auth)/privacy')}
                            className="text-primary-400 underline"
                        >
                            Política de Privacidad
                        </Text>
                    </Text>
                </View>
            </View>

            <CustomButton
                title="Crear cuenta"
                isLoading={isLoading}
                disabled={!isFormValid}
                onPress={handleSignUp}
                variant="primary"
            />

            <View className="flex justify-center mt-5 flex-row gap-2">
                <Text className="text-white/80 font-spacemono text-sm">
                    ¿Ya tienes una cuenta?
                </Text>
                <Link href="/sign-in" asChild>
                    <TouchableOpacity>
                        <Text className="text-primary-400 text-base font-rubik-medium">
                            Iniciar Sesión
                        </Text>
                    </TouchableOpacity>
                </Link>
            </View>
        </View>
    )
}

export default SignUp;
