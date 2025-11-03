import { RANK_IMAGES } from "@/constants/data";
import { TrendingCardProps } from "@/interfaces/interfaces";
import { Image } from "expo-image";
import { Link } from "expo-router";
import { Text, TouchableOpacity, View } from "react-native";

const CARD_WIDTH = 150;
const CARD_HEIGHT = 210;
const RANK_SIZE = 90;
const RANK_OFFSET_LEFT = -40;
const RANK_OFFSET_TOP = -40;

const TrendingCard = ({
    exercise: { exercise_id, title, poster_url },
    index,
}: TrendingCardProps) => {
    const rank = index + 1;

    return (
        <Link href={`/exercises/${exercise_id}`} asChild>
            <TouchableOpacity className="relative pt-12 pb-20 mr-4" activeOpacity={0.85} >
                <View className="relative">
                    <View 
                        className="absolute z-10" 
                        style={{ 
                            left: RANK_OFFSET_LEFT, 
                            top: RANK_OFFSET_TOP 
                        }}
                    >
                        <Image
                            source={RANK_IMAGES[rank]}
                            contentFit="contain"
                            style={{ width: RANK_SIZE, height: RANK_SIZE }}
                        />
                    </View>

                    <View
                        className="rounded-xl overflow-hidden border border-primary-500/20"
                        style={{
                            width: CARD_WIDTH,
                            height: CARD_HEIGHT,
                            shadowColor: '#B8860B',
                            shadowOffset: { width: 0, height: 8 },
                            shadowOpacity: 0.5,
                            shadowRadius: 16,
                            elevation: 12,
                        }}
                    >
                        <Image
                            source={{ uri: poster_url }}
                            contentFit="cover"
                            style={{ width: CARD_WIDTH, height: CARD_HEIGHT }}
                            autoplay={false}
                        />
                    </View>
                </View>

                <View className="mt-2" style={{ width: CARD_WIDTH }}>
                    <Text
                        className="text-[16px] font-oswaldbold text-white tracking-tighter uppercase"
                        numberOfLines={1}
                        style={{
                            textShadowColor: 'rgba(0,0,0,0.9)',
                            textShadowOffset: { width: 0, height: 2 },
                            textShadowRadius: 6,
                            letterSpacing: -0.5,
                        }}
                    >
                        {title}
                    </Text>
                </View>
            </TouchableOpacity>
        </Link>
    );
};

export default TrendingCard;