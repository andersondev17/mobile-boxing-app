// utils/validation.ts

export interface ValidationResult {
    isValid: boolean;
    error?: string;
}

export const validateEmail = (email: string): ValidationResult => {
    if (!email.trim()) {
        return { isValid: false, error: 'El email es requerido' };
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return { isValid: false, error: 'Ingrese un email válido' };
    }

    return { isValid: true };
};

export const validatePassword = (password: string): ValidationResult => {
    if (!password) {
        return { isValid: false, error: 'La contraseña es requerida' };
    }

    if (password.length < 6) {
        return { isValid: false, error: 'Mínimo 6 caracteres' };
    }

    return { isValid: true };
};

export const validateName = (name: string): ValidationResult => {
    if (!name.trim()) {
        return { isValid: false, error: 'El nombre es requerido' };
    }

    if (name.trim().length < 2) {
        return { isValid: false, error: 'Nombre muy corto' };
    }

    return { isValid: true };
};

export const normalizeEmail = (email: string): string => {
    return email.trim().toLowerCase();
};