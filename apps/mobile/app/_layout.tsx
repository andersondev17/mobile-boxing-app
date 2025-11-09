import { DatabaseProvider } from "@/components/DatabaseProvider";
import { useAuthStore } from "@/store/authStore";
import { ActionSheetProvider } from "@expo/react-native-action-sheet";
import { useFonts } from "expo-font";
import { SplashScreen, Stack } from "expo-router";
import { useEffect } from "react";
import { StatusBar } from "react-native";
import './globals.css';
export default function RootLayout() {
  const initialize = useAuthStore((state) => state.initialize);

  const [fontLoaded] = useFonts({
    "space-mono": require("../assets/fonts/SpaceMono-Regular.ttf"),
    "OswaldBold": require("../assets/fonts/Oswald-Bold.ttf"),
    "OswaldMedium": require("../assets/fonts/Oswald-Medium.ttf"),
    "OswaldRegular": require("../assets/fonts/Oswald-Regular.ttf"),
    "OswaldLight": require("../assets/fonts/Oswald-Light.ttf"),
    "OswaldExtraLight": require("../assets/fonts/Oswald-ExtraLight.ttf")
  })

  // Initialize auth store on app start
  useEffect(() => {
    initialize();
  }, []);

  useEffect(() => {
    if (fontLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontLoaded])

  if (!fontLoaded) return null

  return (
    <DatabaseProvider>
      <ActionSheetProvider>
        <>
        <StatusBar hidden={true} />

        <Stack screenOptions={{ headerShown: false }} initialRouteName="(auth)">
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
        </Stack>
        </>
      </ActionSheetProvider>
    </DatabaseProvider>
  );
}
