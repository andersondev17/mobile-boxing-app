import { Stack } from "expo-router";
import './globals.css';
export default function RootLayout() {
  return <Stack >
    {/* hidding header */}
    <Stack.Screen
      name="(tabs)"
      options={{ headerShown: false }}
    />
    <Stack.Screen
      name="exercises/[id]"
      options={{ headerShown: false }}
    />
  </Stack>;
}
