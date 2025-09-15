import ExerciseCard from "@/components/ExerciseCard";
import SearchBar from "@/components/SearchBar";
import { fetchExercises } from "@/constants/exercises";
import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import useFetch from "@/services/usefetch";
import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Image, ScrollView, Text, View } from "react-native";
//home route

export default function Index() {
  const router = useRouter();

  const {
    data: exercises,
    loading: exercisesLoading,
    error: exercisesError,
  } = useFetch(()=> fetchExercises({
    query: ''
  }))

  return (
    <View className="flex-1 bg-gymshock-dark-900">
      <Image source={images.pattern} className="flex-1 absolute w-full h-full opacity-25 z-0" resizeMode="cover" />
      <ScrollView className="flex-1 px-5 " showsVerticalScrollIndicator={false} contentContainerStyle={{ minHeight: "100%", paddingBottom: 10 }} >
        <Image source={icons.logo} className="w-16 h-10 mt-20 mb-5 mx-auto" />


        {exercisesLoading ? (
          <ActivityIndicator
            size="large"
            color="#0000ff"
            className="mt-10 self-center"
          />
        ) : exercisesError ? (
          <Text>Error: {exercisesError?.message}</Text>
        ) : (
          <View className="flex-1 mt-5">
            <SearchBar 
              onPress={() => router.push('/search')}
              placeholder={'Que quieres hacer hoy?'}
            />
            <>
              <Text className="text-lg text-white font-bold mt-5 mb-3">Ultimos ejercicios</Text>
              <FlatList
                data={exercises}
                renderItem={({ item }) => (
                  <ExerciseCard 
                    {...item}
                  />
                )}
                keyExtractor={ (item) => item._id.toString() }/* Helps figure out how many items */
                numColumns={3}  
                columnWrapperStyle={{justifyContent: 'flex-start',gap: 20,paddingRight: 5,marginBottom: 10}}
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
