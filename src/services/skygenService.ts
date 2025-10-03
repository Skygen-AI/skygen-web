import { tauriBridge } from '@/lib/tauri-bridge';

export interface AuthResponse {
    success: boolean;
    data?: any;
    error?: string;
}

export interface StatusResponse {
    authenticated: boolean;
    device_enrolled: boolean;
    connected: boolean;
    device_id?: string;
    platform: string;
    desktop_env_available: boolean;
}

export interface LoginData {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface DeviceData {
    device_id: string;
    device_token: string;
    wss_url: string;
    kid: string;
    expires_at: string;
}

export class SkygenService {
    private static instance: SkygenService;

    public static getInstance(): SkygenService {
        if (!SkygenService.instance) {
            SkygenService.instance = new SkygenService();
        }
        return SkygenService.instance;
    }

    private async invokeCommand<T>(command: string, args?: any): Promise<T> {
        return await tauriBridge.invoke(command, args);
    }

    /**
     * Установка зависимостей Python
     */
    async installDependencies(): Promise<string> {
        try {
            const result = await this.invokeCommand<string>('install_dependencies');
            return result;
        } catch (error) {
            throw new Error(`Failed to install dependencies: ${error}`);
        }
    }

    /**
     * Получение статуса системы
     */
    async getStatus(): Promise<StatusResponse> {
        try {
            const response = await this.invokeCommand<StatusResponse>('skygen_get_status');
            return response;
        } catch (error) {
            throw new Error(`Failed to get status: ${error}`);
        }
    }

    /**
     * Регистрация нового пользователя
     */
    async signup(email: string, password: string): Promise<any> {
        try {
            const response = await this.invokeCommand<AuthResponse>('skygen_signup', {
                email,
                password,
            });

            if (!response.success) {
                throw new Error(response.error || 'Signup failed');
            }

            return response.data;
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Signup failed: ${error}`);
        }
    }

    /**
     * Авторизация пользователя
     */
    async login(email: string, password: string): Promise<LoginData> {
        try {
            const response = await this.invokeCommand<AuthResponse>('skygen_login', {
                email,
                password,
            });

            if (!response.success) {
                throw new Error(response.error || 'Login failed');
            }

            const loginData = response.data as LoginData;

            // Сохраняем токены в localStorage
            if (typeof window !== 'undefined') {
                localStorage.setItem('access_token', loginData.access_token);
                localStorage.setItem('refresh_token', loginData.refresh_token);
            }

            return loginData;
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Login failed: ${error}`);
        }
    }

    /**
     * Регистрация устройства
     */
    async enrollDevice(): Promise<DeviceData> {
        try {
            const response = await this.invokeCommand<AuthResponse>('skygen_enroll_device');

            if (!response.success) {
                throw new Error(response.error || 'Device enrollment failed');
            }

            const deviceData = response.data as DeviceData;

            // Сохраняем данные устройства
            if (typeof window !== 'undefined') {
                localStorage.setItem('device_id', deviceData.device_id);
                localStorage.setItem('device_token', deviceData.device_token);
                localStorage.setItem('wss_url', deviceData.wss_url);
            }

            return deviceData;
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Device enrollment failed: ${error}`);
        }
    }

    /**
     * Подключение к WebSocket
     */
    async connect(): Promise<boolean> {
        try {
            const response = await this.invokeCommand<AuthResponse>('skygen_connect');

            if (!response.success) {
                throw new Error(response.error || 'Connection failed');
            }

            return response.data?.connected || false;
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Connection failed: ${error}`);
        }
    }

    /**
     * Проверка авторизации
     */
    isAuthenticated(): boolean {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('access_token');
    }

    /**
     * Проверка регистрации устройства
     */
    isDeviceEnrolled(): boolean {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('device_id');
    }

    /**
     * Получение токена доступа
     */
    getAccessToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('access_token');
    }

    /**
     * Получение ID устройства
     */
    getDeviceId(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('device_id');
    }

    /**
     * Выход из системы
     */
    logout(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('device_id');
        localStorage.removeItem('device_token');
        localStorage.removeItem('wss_url');
    }

    /**
     * Полная настройка: авторизация + регистрация устройства + подключение
     */
    async fullSetup(email: string, password: string, isSignup: boolean = false): Promise<{
        loginData: LoginData;
        deviceData: DeviceData;
        connected: boolean;
    }> {
        try {
            // Шаг 1: Авторизация или регистрация
            let loginData: LoginData;
            if (isSignup) {
                await this.signup(email, password);
                loginData = await this.login(email, password);
            } else {
                loginData = await this.login(email, password);
            }

            // Шаг 2: Регистрация устройства
            const deviceData = await this.enrollDevice();

            // Шаг 3: Подключение к WebSocket
            const connected = await this.connect();

            return {
                loginData,
                deviceData,
                connected,
            };
        } catch (error) {
            // Очищаем данные в случае ошибки
            this.logout();
            throw error;
        }
    }
}
