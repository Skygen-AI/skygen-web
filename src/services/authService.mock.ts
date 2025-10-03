import { User, LoginResponse, AuthError } from './authService';

/**
 * Mock Auth Service - используется только в DEV режиме
 * Имитирует работу реального бэкенда без необходимости его запуска
 */
export class MockAuthService {
    private static instance: MockAuthService;

    public static getInstance(): MockAuthService {
        if (!MockAuthService.instance) {
            MockAuthService.instance = new MockAuthService();
        }
        return MockAuthService.instance;
    }

    /**
     * Mock регистрация - всегда успешна
     */
    async signup(email: string, password: string): Promise<User> {
        console.log('[DEV MODE] Mock signup:', email);
        
        // Имитация задержки сети
        await new Promise(resolve => setTimeout(resolve, 500));
        
        return {
            id: 'mock-user-id',
            email: email,
        };
    }

    /**
     * Mock авторизация - всегда успешна
     */
    async login(email: string, password: string): Promise<LoginResponse> {
        console.log('[DEV MODE] Mock login:', email);
        
        // Имитация задержки сети
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const mockTokens: LoginResponse = {
            access_token: 'mock-access-token-' + Date.now(),
            refresh_token: 'mock-refresh-token-' + Date.now(),
            token_type: 'Bearer',
        };

        // Сохраняем токены в localStorage как и в реальном сервисе
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', mockTokens.access_token);
            localStorage.setItem('refresh_token', mockTokens.refresh_token);
        }

        return mockTokens;
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
        const user = await this.signup(email, password);
        const tokens = await this.login(email, password);

        return { user, tokens };
    }
}


