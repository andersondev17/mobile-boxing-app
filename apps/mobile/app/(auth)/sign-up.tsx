// sign-up.tsx
import CustomButton from "@/components/CustomButton";
import CustomInput from "@/components/CustomInput";
import { Link, router } from "expo-router";
import { useState } from "react";
import { Alert, Text, TouchableOpacity, View } from 'react-native';

const SignUp = () => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [form, setForm] = useState({ name: '', email: '', password: '' });

    const submit = async () => {
        const { name, email, password } = form;
        if (!name || !email || !password) return Alert.alert('Error', 'Por favor, complete todos los campos requeridos.');
        setIsSubmitting(true)
        try {
            //TODO: Call FastAPI Sign-In function
            Alert.alert('Success', 'Cuenta creada con éxito');
            router.replace('/');
        } catch (error: any) {
            Alert.alert('Error', error.message);
        } finally {
            setIsSubmitting(false);
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

            <CustomButton
                title="Crear cuenta"
                isLoading={isSubmitting}
                onPress={submit}
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