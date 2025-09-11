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
        localStorage.setItem('access_token', loginData.access_token);
        localStorage.setItem('refresh_token', loginData.refresh_token);

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
        return !!localStorage.getItem('access_token');
    }

    /**
     * Получение токена доступа
     */
    getAccessToken(): string | null {
        return localStorage.getItem('access_token');
    }

    /**
     * Выход из системы
     */
    logout(): void {
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
