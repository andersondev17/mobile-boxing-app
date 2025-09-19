import { DatabaseProvider } from "@/components/DatabaseProvider";
import { Stack } from "expo-router";
import { StatusBar } from "react-native";
import './globals.css';
export default function RootLayout() {

  return (
    <DatabaseProvider>
      <StatusBar hidden={true} />

      <Stack >
        {/* hidding header */}
        <Stack.Screen
          name="(tabs)"
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="exercises/[id]"
          options={{ headerShown: false }}
        />
      </Stack>
    </DatabaseProvider>
  );
}
