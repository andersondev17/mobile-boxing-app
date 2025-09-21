import ExerciseCard from "@/components/ExerciseCard";
import ListCard from "@/components/ListCard";
import SearchBar from "@/components/SearchBar";
import TrendingCard from "@/components/TrendingCard";
import { icons } from "@/constants/icons";
import { images } from "@/constants/images";
import { fetchEjerciciosFuerza, fetchExercises, fetchTecnicasDefensa, fetchTecnicasGolpeo } from "@/services/exerciseService";
import { getTrendingExercises } from "@/services/search";
import useFetch from "@/services/usefetch";
import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Image, Text, TouchableOpacity, View } from "react-native";

interface Section {
  type: string;
  id: string;
  title?: string;
  data?: any[];
  showAllLink?: string; //  "link Ver todos"
}

const SECTION_TYPES = {
  HEADER: 'header',
  SEARCH: 'search', 
  TRENDING: 'trending',
  TECNICAS_GOLPEO: 'tecnicas_golpeo',
  DEFENSA: 'defensa', 
  FUERZA: 'fuerza',
  EXERCISES: 'exercises'
} as const;

export default function Index() {
  const router = useRouter();

  const {
    data: trendingExercises,
    loading: trendingLoading,
    error: trendingError,
  } = useFetch(getTrendingExercises);

  const {
    data: exercises,
    loading: exercisesLoading,
    error: exercisesError,
  } = useFetch(() => fetchExercises({ query: '' }));

  const {
    data: tecnicasGolpeo,
    loading: golpeoLoading,
    error: golpeoError,
  } = useFetch(fetchTecnicasGolpeo);

  const {
    data: tecnicasDefensa,
    loading: defensaLoading,
    error: defensaError,
  } = useFetch(fetchTecnicasDefensa);

  const {
    data: ejerciciosFuerza,
    loading: fuerzaLoading,
    error: fuerzaError,
  } = useFetch(fetchEjerciciosFuerza);

  //  horizontal
  const buildSections = (): Section[] => {
    const sections: Section[] = [
      { type: SECTION_TYPES.HEADER, id: 'header' },
      { type: SECTION_TYPES.SEARCH, id: 'search' },
    ];


    if (tecnicasGolpeo?.length) {
      sections.push({
        type: SECTION_TYPES.TECNICAS_GOLPEO,
        id: 'tecnicas_golpeo',
        title: 'Técnicas de Golpeo',
        data: tecnicasGolpeo.slice(0, 10),
        showAllLink: '/tecnicas-golpeo'
      });
    }
    
    if (trendingExercises?.length) {
      sections.push({
        type: SECTION_TYPES.TRENDING,
        id: 'trending',
        title: ' POPULARES HOY',
        data: trendingExercises,
      });
    }  

    if (tecnicasDefensa?.length) {
      sections.push({
        type: SECTION_TYPES.DEFENSA,
        id: 'defensa',
        title: 'Defensa',
        data: tecnicasDefensa.slice(0, 4), // Solo 4 para lista vertical
        showAllLink: '/defensa'
      });
    }

    if (ejerciciosFuerza?.length) {
      sections.push({
        type: SECTION_TYPES.FUERZA,
        id: 'fuerza',
        title: 'Fuerza y Acondicionamiento',
        data: ejerciciosFuerza.slice(0, 10),
        showAllLink: '/fuerza'
      });
    }

    if (exercises?.length) {
      sections.push({
        type: SECTION_TYPES.EXERCISES,
        id: 'exercises', 
        title: ' Últimos ejercicios',
        data: exercises.slice(0, 10),
        showAllLink: '/exercises'
      });
    }

    return sections;
  };

const renderSectionHeader = (section: Section) => {
  const { title, showAllLink } = section;
  if (!title) return null;

  return (
    <View className="flex-row justify-between items-center px-5 mb-3">
      <Text className="text-2xl text-white font-oswaldbold">
        {title}
      </Text>
      {showAllLink && (
        <TouchableOpacity 
          onPress={() => router.push(showAllLink as any)}
          className="p-2"
        >
          <Image 
            source={icons.arrow} 
            className="w-6 h-6 bg-primary-500 rounded-xl"
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

  //  horizontal sections
  const renderItem = ({ item }: { item: Section }) => {
    switch (item.type) {
      case SECTION_TYPES.HEADER:
        return (
          <Image 
            source={icons.logo} 
            className="w-16 h-10 mt-20 mb-5 mx-auto" 
          />
        );
      
      case SECTION_TYPES.SEARCH:
        return (
          <View className="px-5 mb-8">
            <SearchBar
              onPress={() => router.push('/search')}
              placeholder="¿Qué quieres hacer hoy?"
            />
          </View>
        );
      
      case SECTION_TYPES.TRENDING:
        return (
          <View className="mb-6">
            {renderSectionHeader(item)}
            <FlatList
              horizontal
              data={item.data}
              renderItem={({ item: trendingItem, index }) => (
                <View style={{ 
                  marginLeft: index === 0 ? 30 : 0, 
                  marginRight: 30
                }}>
                  <TrendingCard exercise={trendingItem} index={index} />
                </View>
              )}
              keyExtractor={(trendingItem, index) => 
                trendingItem.exercise_id?.toString() || `trending-${index}`
              }
              showsHorizontalScrollIndicator={false}
              removeClippedSubviews
              maxToRenderPerBatch={3}
              initialNumToRender={2}
            />
          </View>
        );
    

      case SECTION_TYPES.DEFENSA:
        return (
          <View className="mb-6">
            {renderSectionHeader(item)}
            <View>
              {item.data?.map((exerciseItem) => (
                <ListCard 
                  key={exerciseItem._id} 
                  exercise={exerciseItem} 
                />
              ))}
            </View>
          </View>
        );

      case SECTION_TYPES.TECNICAS_GOLPEO:
      case SECTION_TYPES.FUERZA:
      case SECTION_TYPES.EXERCISES:
        return (
          <View className="mb-6">
            {renderSectionHeader(item)}
            <FlatList
              horizontal
              data={item.data}
              renderItem={({ item: exerciseItem, index }) => (
                <View style={{ 
                  marginLeft: index === 0 ? 20 : 0, 
                  marginRight: 16,
                  width: 120 
                }}>
                  <ExerciseCard {...exerciseItem} />
                </View>
              )}
              keyExtractor={(exerciseItem) => exerciseItem._id}
              showsHorizontalScrollIndicator={false}
              removeClippedSubviews
              maxToRenderPerBatch={3}
              initialNumToRender={3}
              decelerationRate="fast"
            />
          </View>
        );
      
      default:
        return null;
    }
  };

  if (exercisesLoading || trendingLoading || golpeoLoading || defensaLoading || fuerzaLoading) {
    return (
      <View className="flex-1 bg-black justify-center items-center">
        <Image 
          source={images.pattern} 
          className="absolute w-full h-full opacity-25" 
          resizeMode="cover" 
        />
        <ActivityIndicator size="large" color="#FF6B35" />
      </View>
    );
  }

  if (exercisesError || trendingError || golpeoError || defensaError || fuerzaError) {
    return (
      <View className="flex-1 bg-black justify-center items-center px-5">
        <Image 
          source={images.pattern} 
          className="absolute w-full h-full opacity-25" 
          resizeMode="cover" 
        />
        <Text className="text-white text-center">
          Error: {exercisesError?.message || trendingError?.message}
        </Text>
      </View>
    );
  }

  const sections = buildSections();

  return (
    <View className="flex-1 bg-black">
      <Image
        source={images.bg}
        className="absolute w-full h-full opacity-25 bg-backgroundImage-premiumGradient"
        resizeMode="cover"
      />
      
      <FlatList
        data={sections}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 120 }}
        removeClippedSubviews
        maxToRenderPerBatch={2}
        initialNumToRender={2}
        windowSize={3}
      />
    </View>
  );
}