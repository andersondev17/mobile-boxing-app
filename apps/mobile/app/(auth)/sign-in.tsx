// sign-in.tsx
import CustomButton from "@/components/CustomButton";
import CustomInput from "@/components/CustomInput";
import { Link, router } from "expo-router";
import { useState } from "react";
import { Alert, Text, View } from 'react-native';

const SignIn = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });

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
    <View className="gap-10 bg-gymshock-dark-800/95 border border-white/5 rounded-3xl p-6 mt-5 mx-5">
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
        title="Iniciar Sesión"
        isLoading={isSubmitting}
        onPress={submit}
      />

      <View className="flex justify-center mt-5 flex-row gap-2">
        <Text className="text-white/80 font-spacemono text-sm">
          ¿No tienes una cuenta?
        </Text>
        <Link href="/sign-up" className="text-primary-400 font-oswaldmed text-sm">
          Regístrate
        </Link>
      </View>
    </View>
  )
}

export default SignIn