import ListCard from '@/components/ListCard'
import SearchBar from '@/components/SearchBar'
import { icons } from '@/constants/icons'
import { images } from '@/constants/images'
import { fetchExercises } from '@/services/exerciseService'
import { updateSearchCount } from '@/services/search'
import useFetch from '@/services/usefetch'
import { router } from 'expo-router'
import { useEffect, useRef, useState } from 'react'
import { ActivityIndicator, FlatList, Image, Text, View } from 'react-native'

const Search = () => {
    const [searchQuery, setSearchQuery] = useState('')
    const lastUpdateQuery = useRef('')
    const {
        data: exercises,
        loading,
        error,
        refetch: loadExercises,
        reset,
    } = useFetch(() => fetchExercises({
        query: searchQuery
    }), false)

    const exerciseList = exercises || []

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
        const query = searchQuery.trim()
        if (exerciseList.length > 0 && query && query !== lastUpdateQuery.current) {
            updateSearchCount(query, exerciseList[0])
            lastUpdateQuery.current = query
        }
    }, [exerciseList, searchQuery])

    return (
        <View className='bg-gymshock-dark-900 flex-1'>
            <Image source={images.bg} className="flex-1 absolute w-full h-full opacity-25 z-0" resizeMode="cover" />

            <FlatList
                data={exerciseList}
                renderItem={({ item }) => (<ListCard exercise={item} />)}
                keyExtractor={(item) => item._id.toString()}
                className='px-5'
                contentContainerStyle={{
                    paddingBottom: 100,
                }}
                ItemSeparatorComponent={() => <View className="h-3" />}  

                ListHeaderComponent={
                    <>

                        <View className='bg-gymshock-dark-800/95  -mx-5 px-5 pt-16 pb-4'>
                            <SearchBar
                                placeholder='¿Que quieres hacer hoy?'
                                value={searchQuery}
                                onChangeText={handleSearch}
                                showCancel={true}
                                autoFocus={true}
                                onCancel={() => router.back()}
                            />
                        </View>
                        {loading && (
                            <ActivityIndicator size="large" color="#0000ff" className="my-3" />
                        )}
                        {error && (
                            <Text className='text-red-500 px-5 my-3 font-oswald'>Error: {error.message}</Text>
                        )}
                        {!loading && !error && searchQuery.trim() && exerciseList.length > 0 && (
                            <View className="flex-row items-center gap-2 px-5 pb-5 py-4">
                                <Image source={icons.search} className="size-5" resizeMode="contain" tintColor="#abd8bff" />
                                <Text className="text-base text-white font-spacemono "> {searchQuery} </Text>
                            </View>
                        )}
                    </>
                }
                ListEmptyComponent={
                    !loading && !error ? (
                        <View className="mt-10 px-5">
                            <Text className="text-center text-gray-500 font-oswald">
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