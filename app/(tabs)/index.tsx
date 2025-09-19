import ExerciseCard from "@/components/ExerciseCard";
import SearchBar from "@/components/SearchBar";
import TrendingCard from "@/components/TrendingCard";
import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import { fetchExercises } from "@/services/exerciseService";
import { getTrendingExercises } from "@/services/search";
import useFetch from "@/services/usefetch";
import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Image, ScrollView, Text, View } from "react-native";
//home route

export default function Index() {
  const router = useRouter();

  const {
    data: trendingExercises,
    loading: trendingLoading,
    error: trendingError,
  } = useFetch((getTrendingExercises))
  const {
    data: exercises,
    loading: exercisesLoading,
    error: exercisesError,
  } = useFetch(() => fetchExercises({
    query: ''
  }))

  return (
    <View className="flex-1 bg-gymshock-dark-900">
      <Image source={images.pattern} className="flex-1 absolute w-full h-full opacity-25 z-0" resizeMode="cover" />
      <ScrollView className="flex-1 px-5 " showsVerticalScrollIndicator={false} contentContainerStyle={{ minHeight: "100%", paddingBottom: 10 }} >
        <Image source={icons.logo} className="w-16 h-10 mt-20 mb-5 mx-auto" />


        {exercisesLoading || trendingLoading ? (
          <ActivityIndicator
            size="large"
            color="#0000ff"
            className="mt-10 self-center"
          />
        ) : exercisesError || trendingError ? (
          <Text>Error: {exercisesError?.message || trendingError?.message}</Text>
        ) : (
          <View className="flex-1 mt-5">
            <SearchBar
              onPress={() => router.push('/search')}
              placeholder={'Que quieres hacer hoy?'}
            />
            {trendingExercises && (
              <View className="mt-10">
                <Text className="text-lg text-white font-bold mb-3">Ejercicios populares</Text>
              </View>
            )}
            <>
              <FlatList
                className="mb-4 mt-3"
                horizontal
                showsHorizontalScrollIndicator={false}
                data={trendingExercises}
                contentContainerStyle={{ gap: 26 }}
                renderItem={({ item, index }) => (
                  <TrendingCard exercise={item} index={index}/>
                )}
                keyExtractor={(item, index) => item.exercise_id?.toString() || index.toString()}
                ItemSeparatorComponent={() => <View className="w-4" />}
              />
              <Text className="text-lg text-white font-bold mt-5 mb-3">Ultimos ejercicios</Text>

              <FlatList
                data={exercises}
                renderItem={({ item }) => (
                  <ExerciseCard
                    {...item}
                  />
                )}
                keyExtractor={(item) => item._id.toString()}/* Helps figure out how many items */
                numColumns={3}
                columnWrapperStyle={{ justifyContent: 'flex-start', gap: 20, paddingRight: 5, marginBottom: 10 }}
                className="mt-2 pb-32"
                scrollEnabled={false}
              />
            </>
          </View>
        )
        }

      </ScrollView>
    </View>
  );
}
