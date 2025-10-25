import MaskedView from "@react-native-masked-view/masked-view";
import { Link } from "expo-router";

import { images } from "@/constants/images";
import { TrendingCardProps } from "@/interfaces/interfaces";
import { Image } from "expo-image";
import { Text, TouchableOpacity, View } from "react-native";

const TrendingCard = ({
    exercise: { exercise_id, title, poster_url },
    index,
}: TrendingCardProps) => {
    const displayNumber = index + 1;
    const isDoubleDigit = displayNumber >= 10;
    
    return (
        <Link href={`/exercises/${exercise_id}`} asChild>
            <TouchableOpacity className="w-[180px] relative pb-20"  activeOpacity={0.85}>
                <View
                    className="absolute top-10 z-0"
                    style={{
                        left: isDoubleDigit ? -70 : -15,
                        shadowColor: '#B8860B',
                        shadowOffset: { width: 0, height: 18 },
                        shadowOpacity: 0.3,
                        shadowRadius: 30,
                        elevation: 20,
                        opacity: 0.10,  // para números dobles
                    }}
                >
                    <MaskedView
                        style={{
                            width: isDoubleDigit ? 180 : 150,
                            height: 220
                        }}
                        maskElement={
                            <Text
                                style={{
                                    fontSize: 200,
                                    fontFamily: 'OswaldBold',
                                    color: 'white',
                                    textAlign: 'left',
                                    letterSpacing: -10,
                                }}
                            >
                                {displayNumber}
                            </Text>
                        }
                    >
                        <Image
                            source={images.rankingGradient}
                            className="size-full"
                            contentFit="cover"
                            style={{ width: 150, height: 210 }}

                        />
                    </MaskedView>
                </View>

                <View
                    className="relative z-10 rounded-xl overflow-hidden ml-16 border border-primary-500/20"
                    style={{
                        shadowColor: '#B8860B',
                        shadowOffset: { width: 0, height: 8 },
                        shadowOpacity: 0.5,
                        shadowRadius: 16,
                        elevation: 12,
                    }}
                >
                    <Image
                        source={{ uri: poster_url }}
                        className="w-[150px] h-[210px]"
                        contentFit="cover"
                        style={{ width: 150, height: 210 }}
                        autoplay={false}
                    />
                </View>

                {/* Título con shadow */}
                <View className="relative z-10 mt-2 ml-16">
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