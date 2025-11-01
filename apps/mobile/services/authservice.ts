// services/authService.js

interface LoginResponse {
    token: string;
    user: {
        id: number;
        name: string;
        email: string;
    };
}

export async function mockLogin(email: string, password: string): Promise<LoginResponse> {
    // Simula una petición exitosa
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                token: "fake-jwt-token",
                user: {
                    id: 1,
                    name: "Usuario Demo",
                    email,
                },
            });
        }, 1000);
    });
}
