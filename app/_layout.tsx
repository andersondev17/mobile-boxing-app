import { DatabaseProvider } from "@/components/DatabaseProvider";
import { useFonts } from "expo-font";
import { SplashScreen, Stack } from "expo-router";
import { useEffect } from "react";
import { StatusBar } from "react-native";
import './globals.css';
export default function RootLayout() {
  const [fontLoaded] = useFonts({
    "space-mono": require("../assets/fonts/SpaceMono-Regular.ttf"),
    "OswaldBold": require("../assets/fonts/Oswald-Bold.ttf"),
    "OswaldMedium": require("../assets/fonts/Oswald-Medium.ttf"),
    "OswaldRegular": require("../assets/fonts/Oswald-Regular.ttf"),
    "OswaldLight": require("../assets/fonts/Oswald-Light.ttf"),
    "OswaldExtraLight": require("../assets/fonts/Oswald-ExtraLight.ttf")
  })
  useEffect(() => {
    if (fontLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontLoaded])

  if (!fontLoaded) return null

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
