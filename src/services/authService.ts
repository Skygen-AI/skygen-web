import { websocketService } from './websocketService';

export interface User {
    id: string;
    email: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface AuthError {
    detail: string;
}

/**
 * Real Auth Service - подключается к реальному бэкенду
 * Используется в продакшене или когда DEV_MODE отключен
 */
export class AuthService {
    private static instance: AuthService;
    private backendUrl: string = 'http://localhost:8000';

    public static getInstance(): AuthService {
        if (!AuthService.instance) {
            AuthService.instance = new AuthService();
        }
        return AuthService.instance;
    }

    /**
     * Регистрация нового пользователя
     */
    async signup(email: string, password: string): Promise<User> {
        const response = await fetch(`${this.backendUrl}/v1/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        if (!response.ok) {
            const errorData: AuthError = await response.json();
            throw new Error(errorData.detail || 'Registration failed');
        }

        const user: User = await response.json();
        return user;
    }

    /**
     * Авторизация пользователя
     */
    async login(email: string, password: string): Promise<LoginResponse> {
        const response = await fetch(`${this.backendUrl}/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        if (!response.ok) {
            const errorData: AuthError = await response.json();
            throw new Error(errorData.detail || 'Login failed');
        }

        const loginData: LoginResponse = await response.json();

        // Сохраняем токены в localStorage
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', loginData.access_token);
            localStorage.setItem('refresh_token', loginData.refresh_token);
        }

        // Подключаемся к WebSocket с полученным токеном
        try {
            await websocketService.connect(loginData.access_token);
            console.log('WebSocket connected successfully');
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            // Не прерываем логин если WebSocket не подключился
        }

        return loginData;
    }

    /**
     * Проверка авторизации
     */
    isAuthenticated(): boolean {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('access_token');
    }

    /**
     * Получение токена доступа
     */
    getAccessToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('access_token');
    }

    /**
     * Выход из системы
     */
    logout(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    /**
     * Полный процесс: регистрация + авторизация
     */
    async signupAndLogin(email: string, password: string): Promise<{
        user: User;
        tokens: LoginResponse;
    }> {
        // Сначала регистрируемся
        const user = await this.signup(email, password);
        
        // Затем авторизуемся
        const tokens = await this.login(email, password);

        return { user, tokens };
    }
}

// ============================================
// Conditional Export: Mock vs Real Service
// ============================================
// В DEV режиме используем mock-сервис (без бэкенда)
// В PROD режиме используем реальный сервис
// 
// ВАЖНО: Проверка использует строгое сравнение === 'true'
// Любое другое значение (включая undefined) = PROD режим
import { MockAuthService } from './authService.mock';

const isDev = process.env.NEXT_PUBLIC_DEV_MODE === 'true';

// В dev-режиме экспортируем mock, иначе - реальный сервис
export const authService = isDev 
    ? MockAuthService.getInstance()
    : AuthService.getInstance();

// Логируем режим только один раз
if (typeof window !== 'undefined') {
    console.log(
        `[AuthService] Mode: ${isDev ? '🔧 DEV (Mock)' : '🚀 PRODUCTION (Real Backend)'}`
    );
}
