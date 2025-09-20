import MaskedView from "@react-native-masked-view/masked-view";
import { Link } from "expo-router";
import { Image, Text, TouchableOpacity, View } from "react-native";

import { images } from "@/constants/images";
import { TrendingCardProps } from "@/interfaces/interfaces";

const TrendingCard = ({
    exercise: { exercise_id, title, poster_url },
    index,
}: TrendingCardProps) => {
    const displayNumber = index + 1;
    const isDoubleDigit = displayNumber >= 10;
    
    return (
        <Link href={`/exercises/${exercise_id}`} asChild>
            <TouchableOpacity className="w-32 relative pl-3" activeOpacity={0.85}>
                <View 
                    className="absolute -top-1 z-0 shadow-xl shadow-black"
                    style={{ 
                        left: isDoubleDigit ? -52 : -24, //  para números dobles
                    }}
                >
                    <MaskedView
                        style={{ 
                            width: isDoubleDigit ? 120 : 100, // Ancho dinámico
                            height: 120 
                        }}
                        maskElement={
                            <Text className="font-oswaldbold text-white text-8xl">
                                {displayNumber}
                            </Text>
                        }
                    >
                        <Image
                            source={images.rankingGradient}
                            className="size-full"
                            resizeMode="cover"
                        />
                    </MaskedView>
                </View>

                <View className="relative z-10 shadow-xl shadow-black">
                    <Image
                        source={{ uri: poster_url }}
                        className="w-32 h-48 rounded-lg"
                        resizeMode="cover"
                    />
                </View>

                <Text
                    className="text-sm font-oswaldmed mt-2 text-white/90 relative z-10"
                    numberOfLines={2}
                >
                    {title}
                </Text>
            </TouchableOpacity>
        </Link>
    );
};

export default TrendingCard;