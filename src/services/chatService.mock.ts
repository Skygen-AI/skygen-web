import { 
    ChatSession, 
    ChatMessage, 
    ChatSessionWithMessages, 
    AgentChatResponse,
    AgentCapabilities 
} from './chatService';

/**
 * Mock Chat Service - используется только в DEV режиме
 * Имитирует работу реального бэкенда с предустановленными данными
 */
export class MockChatService {
    private static instance: MockChatService;
    private deviceId: string;
    private mockSessions: ChatSession[] = [];
    private mockMessages: Map<string, ChatMessage[]> = new Map();

    private constructor() {
        this.deviceId = typeof window !== 'undefined' ? this.getOrCreateDeviceId() : '';
        if (typeof window !== 'undefined') {
            this.initializeMockData();
        }
    }

    public static getInstance(): MockChatService {
        if (!MockChatService.instance) {
            MockChatService.instance = new MockChatService();
        }
        return MockChatService.instance;
    }

    private getOrCreateDeviceId(): string {
        if (typeof window === 'undefined') {
            return '';
        }
        
        const stored = localStorage.getItem('device_id');
        if (stored) return stored;
        
        const newDeviceId = 'mock-device-' + Date.now();
        localStorage.setItem('device_id', newDeviceId);
        return newDeviceId;
    }

    private initializeMockData(): void {
        // Создаём пример чат-сессии
        const welcomeSession: ChatSession = {
            id: 'mock-session-1',
            user_id: 'mock-user-id',
            device_id: this.deviceId,
            title: 'Welcome Chat',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true,
            metadata: {},
            message_count: 2,
        };

        this.mockSessions.push(welcomeSession);

        // Добавляем примеры сообщений
        this.mockMessages.set('mock-session-1', [
            {
                id: 'msg-1',
                session_id: 'mock-session-1',
                role: 'assistant',
                content: '👋 Привет! Я AI ассистент Skygen в режиме разработки. Все данные сейчас мок-данные. Задавайте любые вопросы!',
                created_at: new Date(Date.now() - 60000).toISOString(),
                metadata: {},
            },
        ]);
    }

    async createSession(title: string, deviceId?: string): Promise<ChatSession> {
        console.log('[DEV MODE] Mock createSession:', title);
        await new Promise(resolve => setTimeout(resolve, 300));

        const session: ChatSession = {
            id: 'mock-session-' + Date.now(),
            user_id: 'mock-user-id',
            device_id: deviceId || this.deviceId,
            title,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true,
            metadata: {},
            message_count: 0,
        };

        this.mockSessions.push(session);
        this.mockMessages.set(session.id, []);

        return session;
    }

    async getSessions(limit = 50, offset = 0, activeOnly = true): Promise<ChatSession[]> {
        console.log('[DEV MODE] Mock getSessions');
        await new Promise(resolve => setTimeout(resolve, 200));

        let sessions = [...this.mockSessions];
        if (activeOnly) {
            sessions = sessions.filter(s => s.is_active);
        }

        return sessions.slice(offset, offset + limit);
    }

    async getSession(sessionId: string): Promise<ChatSessionWithMessages> {
        console.log('[DEV MODE] Mock getSession:', sessionId);
        await new Promise(resolve => setTimeout(resolve, 200));

        const session = this.mockSessions.find(s => s.id === sessionId);
        if (!session) {
            throw new Error('Session not found');
        }

        const messages = this.mockMessages.get(sessionId) || [];

        return {
            ...session,
            messages,
        };
    }

    async addMessage(
        sessionId: string,
        content: string,
        role: 'user' | 'assistant' | 'system' = 'user'
    ): Promise<ChatMessage> {
        console.log('[DEV MODE] Mock addMessage:', { sessionId, content, role });
        await new Promise(resolve => setTimeout(resolve, 200));

        const message: ChatMessage = {
            id: 'msg-' + Date.now(),
            session_id: sessionId,
            role,
            content,
            created_at: new Date().toISOString(),
            metadata: {},
        };

        const messages = this.mockMessages.get(sessionId) || [];
        messages.push(message);
        this.mockMessages.set(sessionId, messages);

        // Обновляем счётчик сообщений
        const session = this.mockSessions.find(s => s.id === sessionId);
        if (session) {
            session.message_count = messages.length;
            session.updated_at = new Date().toISOString();
        }

        return message;
    }

    async updateSession(
        sessionId: string,
        updates: {
            title?: string;
            is_active?: boolean;
            metadata?: Record<string, any>;
        }
    ): Promise<ChatSession> {
        console.log('[DEV MODE] Mock updateSession:', { sessionId, updates });
        await new Promise(resolve => setTimeout(resolve, 200));

        const session = this.mockSessions.find(s => s.id === sessionId);
        if (!session) {
            throw new Error('Session not found');
        }

        Object.assign(session, updates, { updated_at: new Date().toISOString() });
        return session;
    }

    async deleteSession(sessionId: string): Promise<void> {
        console.log('[DEV MODE] Mock deleteSession:', sessionId);
        await new Promise(resolve => setTimeout(resolve, 200));

        const index = this.mockSessions.findIndex(s => s.id === sessionId);
        if (index !== -1) {
            this.mockSessions.splice(index, 1);
            this.mockMessages.delete(sessionId);
        }
    }

    async chatWithAgent(
        message: string,
        sessionId?: string,
        deviceId?: string
    ): Promise<AgentChatResponse> {
        console.log('[DEV MODE] Mock chatWithAgent:', { message, sessionId });
        
        // Имитация задержки обработки
        await new Promise(resolve => setTimeout(resolve, 800));

        let activeSessionId = sessionId;
        
        // Создаём новую сессию если её нет
        if (!activeSessionId) {
            const newSession = await this.createSession(
                message.slice(0, 50) + (message.length > 50 ? '...' : ''),
                deviceId
            );
            activeSessionId = newSession.id;
        }

        // Добавляем сообщение пользователя
        const userMessage = await this.addMessage(activeSessionId, message, 'user');

        // Генерируем ответ ассистента
        const aiResponses = [
            '🤖 Это мок-ответ AI ассистента. В реальном режиме здесь будет настоящий ответ от агента.',
            '✨ В dev-режиме я использую заготовленные ответы. Запустите бэкенд для полного функционала!',
            '💡 Отличный вопрос! В продакшн-режиме я смогу действительно помочь с этим.',
            '🔧 Сейчас работает mock-сервис. Все функции будут доступны после подключения к реальному бэкенду.',
        ];

        const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
        const assistantMessage = await this.addMessage(activeSessionId, randomResponse, 'assistant');

        return {
            session_id: activeSessionId,
            message: userMessage,
            assistant_message: assistantMessage,
            task_created: false,
        };
    }

    async getAgentCapabilities(): Promise<AgentCapabilities> {
        console.log('[DEV MODE] Mock getAgentCapabilities');
        await new Promise(resolve => setTimeout(resolve, 200));

        return {
            capabilities: [
                {
                    name: 'Mock Chat',
                    description: 'Basic chat in dev mode',
                    keywords: ['chat', 'talk', 'ask'],
                    example: 'Ask me anything',
                },
            ],
            supported_languages: ['en', 'ru'],
            version: 'mock-1.0.0',
            agent_type: 'mock',
        };
    }

    async getMessages(
        sessionId: string,
        limit = 100,
        offset = 0
    ): Promise<ChatMessage[]> {
        console.log('[DEV MODE] Mock getMessages:', sessionId);
        await new Promise(resolve => setTimeout(resolve, 200));

        const messages = this.mockMessages.get(sessionId) || [];
        return messages.slice(offset, offset + limit);
    }
}

export const mockChatService = MockChatService.getInstance();


