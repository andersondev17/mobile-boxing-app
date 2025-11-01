// sign-up.tsx
import CustomButton from "@/components/CustomButton";
import CustomInput from "@/components/CustomInput";
import { Link, router } from "expo-router";
import { useState } from "react";
import { Alert, Text, View } from 'react-native';

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
        <View className="gap-10 bg-gymshock-dark-800/95 border border-white/5 rounded-3xl p-6 mt-5 mx-5">
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
                secureTextEntry={true}
            />

            <CustomButton
                title="Regístrate"
                isLoading={isSubmitting}
                onPress={submit}
            />

            <View className="flex justify-center mt-5 flex-row gap-2">
                <Text className="text-white/80 font-spacemono text-sm">
                    ¿Ya tienes una cuenta?
                </Text>
                <Link href="/sign-in" className="text-primary-400 font-oswaldmed text-sm">
                    Iniciar Sesión
                </Link>
            </View>
        </View>
    )
}

export default SignUp;