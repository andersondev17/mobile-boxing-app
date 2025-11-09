import AuthContainer from '@/components/AuthContainer';
import { useAuthStore } from '@/store/authStore';
import { Redirect, Slot } from "expo-router";

export default function AuthLayout() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    if (isAuthenticated) return <Redirect href="/" />

    return (
        <AuthContainer>
            <Slot />
        </AuthContainer>
    );
}