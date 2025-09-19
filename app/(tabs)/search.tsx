import ExerciseCard from '@/components/ExerciseCard'
import SearchBar from '@/components/SearchBar'
import { icons } from '@/constants/icons'
import { images } from '@/constants/images'
import { fetchExercises } from '@/services/exerciseService'
import { updateSearchCount } from '@/services/search'
import useFetch from '@/services/usefetch'
import { useEffect, useState } from 'react'
import { ActivityIndicator, FlatList, Image, Text, View } from 'react-native'

const Search = () => {
    const [searchQuery, setSearchQuery] = useState('')
    const {
        data: exercises = [],
        loading,
        error,
        refetch: loadExercises,
        reset,
    } = useFetch(() => fetchExercises({
        query: searchQuery
    }), false)

    const handleSearch = (text: string) => {
        setSearchQuery(text)
    }

    // Debounced search effect
    useEffect(() => {
        const timeoutId = setTimeout(async () => {
            if (searchQuery.trim()) {
                await loadExercises()
            } else {
                reset()
            }
        }, 500)
        return () => clearTimeout(timeoutId)
    }, [searchQuery, loadExercises, reset])

    useEffect(() => {
        if (exercises && exercises.length > 0 && exercises[0]) {
            updateSearchCount(searchQuery, exercises[0])
        }
    }, [exercises, searchQuery])

    return (
        <View className='bg-gymshock-dark-900 flex-1'>
            <Image source={images.pattern} className="flex-1 absolute w-full h-full opacity-25 z-0" resizeMode="cover" />
            <FlatList
                data={exercises || []}
                renderItem={({ item }) => (<ExerciseCard {...item} />)}
                keyExtractor={(item) => item._id.toString()}
                className='px-5'
                numColumns={3}
                columnWrapperStyle={{
                    justifyContent: 'center',
                    gap: 16,
                    marginVertical: 16
                }}
                contentContainerStyle={{
                    paddingBottom: 100
                }}
                ListHeaderComponent={
                    <>
                        <View className='w-full flex-row justify-center mt-20'>
                            <Image source={icons.logo} className="w-12 h-10" />
                        </View>
                        <View className='my-5'>
                            <SearchBar
                                placeholder='Busca un ejercicio...'
                                value={searchQuery}
                                onChangeText={handleSearch}
                            />
                        </View>
                        {loading && (
                            <ActivityIndicator size="large" color="#0000ff" className="my-3" />
                        )}
                        {error && (
                            <Text className='text-red-500 px-5 my-3'>Error: {error.message}</Text>
                        )}
                        {!loading && !error && searchQuery.trim() && exercises && exercises.length > 0 && (
                            <Text className='text-xl text-white font-bold'>
                                Buscaste {' '}
                                <Text className='text-accent-cosmic'>{searchQuery}</Text>
                            </Text>
                        )}
                    </>
                }
                ListEmptyComponent={
                    !loading && !error ? (
                        <View className="mt-10 px-5">
                            <Text className="text-center text-gray-500">
                                {searchQuery.trim()
                                    ? "No se encontraron ejercicios"
                                    : "Escribe para buscar ejercicios"}
                            </Text>
                        </View>
                    ) : null
                }
            />
        </View>
    )
}

export default Search