// sign-in.tsx
import CustomButton from "@/components/CustomButton";
import CustomInput from "@/components/CustomInput";
import { icons } from "@/constants/icons";
import { Link, router } from "expo-router";
import { useState } from "react";
import { Alert, Image, Text, TouchableOpacity, View } from 'react-native';

const SignIn = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });
    const [showManualForm, setShowManualForm] = useState(false);

  const submit = async () => {
    const { email, password } = form;
    if (!email || !password) return Alert.alert('Error', 'Por favor, ingrese un email y una contraseña válida.');
    setIsSubmitting(true)
    try {
      //TODO: Call FastAPI Sign-In function
      Alert.alert('Success', 'Iniciaste sesión con éxito');
      router.replace('/');
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

    return (
        <View className="px-6 pt-8 pb-12">
            {/* Header */}
            <View className="mb-8">
                <Text className="text-white text-4xl font-oswaldbold text-center mb-2">
                    Inicia sesión
                </Text>
                <Text className="text-white/60 text-sm font-spacemono font-medium tracking-wider mb-2 text-center">
                    Bienvenido de Vuelta
                </Text>
            </View>

            {/* Google Sign-In */}
            <TouchableOpacity
                onPress={submit}
                className="bg-white rounded-2xl py-4 mb-6 shadow-lg shadow-black/50"
                activeOpacity={0.7}
            >
                <View className="flex-row items-center justify-center">
                    <Image
                        source={icons.google}
                        className="w-5 h-5"
                        resizeMode="contain"
                    />
                    <Text className="text-black font-spacemono font-medium text-base tracking-wide ml-3">
                        Continuar con Google
                    </Text>
                </View>
            </TouchableOpacity>

            {/* Manual Form (conditional) */}
            {showManualForm && (
                <>
                    <View className="gap-4 mb-4">
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
                    </View>

                    <TouchableOpacity className="mb-6">
                        <Text className="text-primary-400 text-sm font-rubik-medium text-right">
                            ¿Olvidaste tu contraseña?
                        </Text>
                    </TouchableOpacity>
                </>
            )}

            <CustomButton
                title={showManualForm ? "Iniciar Sesión" : "Continuar con Email"}
                isLoading={isSubmitting}
                onPress={showManualForm ? submit : () => setShowManualForm(true)}
                variant="primary"
            />

            <View className="flex-row justify-center mt-6">
                <Text className="text-white/60 text-base font-spacemono">
                    ¿No tienes una cuenta?{' '}
                </Text>
                <Link href="/sign-up" asChild>
                    <TouchableOpacity>
                        <Text className="text-primary-400 text-base font-rubik-medium">
                            Regístrate
                        </Text>
                    </TouchableOpacity>
                </Link>
            </View>
        </View>
    )
}

export default SignIn