import CustomButton from '@/components/CustomButton';
import { BUTTON_TEXT, LEGAL_FOOTER, TERMS_SECTIONS } from '@/constants/legal';
import { Stack, useRouter } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';

export default function TermsScreen() {
  const router = useRouter();

  return (
    <ScrollView className="flex-1 bg-white px-6 py-4">
      <Stack.Screen
        options={{
          title: 'Términos y Condiciones',
          headerShown: true,
        }}
      />

      <Text className="text-2xl font-bold mb-4">
        Términos y Condiciones de Uso
      </Text>
      <Text className="text-sm text-gray-600 mb-6">
        Última actualización: {new Date().toLocaleDateString('es-CO')}
      </Text>

      {/* Render sections dynamically */}
      {TERMS_SECTIONS.map((section) => (
        <View key={section.id} className="mb-6">
          <Text className="text-lg font-semibold mb-2">
            {section.id}. {section.title}
          </Text>
          <Text className="text-base text-gray-700 leading-6">
            {section.content}
          </Text>
        </View>
      ))}

      <Text className="text-xs text-gray-500 text-center mb-6">
        {LEGAL_FOOTER.terms}
      </Text>

      {/* Close Button */}
      <View className="mb-8 px-4">
        <CustomButton
          title={BUTTON_TEXT.understood}
          onPress={() => router.back()}
          variant="primary"
        />
      </View>
    </ScrollView>
  );
}
