import { Models } from "react-native-appwrite";



interface CustomButtonProps {
    onPress?: () => void;
    title?: string;
    style?: string;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
    textStyle?: string;
    isLoading?: boolean;
    variant?: "default" | "primary";
}

interface CustomInputProps {
    placeholder?: string;
    value?: string;
    onChangeText?: (text: string) => void;
    label: string;
    secureTextEntry?: boolean;
    keyboardType?: "default" | "email-address" | "numeric" | "phone-pad";
    error?: boolean;
    errorMessage?: string;
}
export interface MenuItem extends Models.Document {
    name: string;
    price: number;
    image_url: string;
    description: string;
    calories: number;
    protein: number;
    rating: number;
    type: string;
}

export interface Category extends Models.Document {
    name: string;
    description: string;
}

export interface User extends Models.Document {
    name: string;
    email: string;
    avatar: string;
}

interface TabBarIconProps {
    focused: boolean;
    icon: ImageSourcePropType;
    title: string;
}

interface CustomHeaderProps {
    title?: string;
}


interface ProfileFieldProps {
    label: string;
    value: string;
    icon: ImageSourcePropType;
}


interface GetMenuParams {
    category: string;
    query: string;
}

interface LoginRequest {
    email: string;
    password: string;
}

interface RegisterRequest {
    name: string;
    email: string;
    password: string;
}

interface AuthResponse {
    token: string;
    user: {
        id: number;
        name: string;
        email: string;
        avatar?: string;
    };
}

interface AuthError {
    message: string;
    field?: string;
}