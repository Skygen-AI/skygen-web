// No Tauri dependency needed for HTTP-based ChatService

export interface ChatSession {
    id: string;
    user_id: string;
    device_id?: string;
    title: string;
    created_at: string;
    updated_at: string;
    is_active: boolean;
    metadata: Record<string, any>;
    message_count?: number;
}

export interface ChatMessage {
    id: string;
    session_id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    created_at: string;
    metadata: Record<string, any>;
    task_id?: string;
}

export interface ChatSessionWithMessages extends ChatSession {
    messages: ChatMessage[];
}

export interface AgentChatResponse {
    session_id: string;
    message: ChatMessage;
    assistant_message?: ChatMessage;
    task_created: boolean;
    task_id?: string;
}

export interface AgentCapabilities {
    capabilities: Array<{
        name: string;
        description: string;
        keywords: string[];
        example: string;
    }>;
    supported_languages: string[];
    version: string;
    agent_type: string;
}

export class ChatService {
    private static instance: ChatService;
    private backendUrl: string = 'http://localhost:8000';
    private deviceId: string;

    private constructor() {
        // Получаем или создаем device_id
        this.deviceId = this.getOrCreateDeviceId();
    }

    public static getInstance(): ChatService {
        if (!ChatService.instance) {
            ChatService.instance = new ChatService();
        }
        return ChatService.instance;
    }

    private getOrCreateDeviceId(): string {
        const stored = localStorage.getItem('device_id');
        if (stored) {
            return stored;
        }
        
        // Генерируем новый device_id как UUID
        const newDeviceId = this.generateUUID();
        localStorage.setItem('device_id', newDeviceId);
        return newDeviceId;
    }

    private generateUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('Not authenticated');
        }
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        };
    }

    /**
     * Создание новой чат-сессии
     */
    async createSession(title: string, deviceId?: string): Promise<ChatSession> {
        const response = await fetch(`${this.backendUrl}/v1/chat/sessions`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                title,
                device_id: deviceId,
                metadata: {},
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Получение списка чат-сессий
     */
    async getSessions(limit = 50, offset = 0, activeOnly = true): Promise<ChatSession[]> {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
            active_only: activeOnly.toString(),
        });

        const response = await fetch(`${this.backendUrl}/v1/chat/sessions?${params}`, {
            headers: this.getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Failed to get sessions: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Получение чат-сессии с сообщениями
     */
    async getSession(sessionId: string): Promise<ChatSessionWithMessages> {
        const response = await fetch(`${this.backendUrl}/v1/chat/sessions/${sessionId}`, {
            headers: this.getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Failed to get session: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Добавление сообщения в чат
     */
    async addMessage(
        sessionId: string,
        content: string,
        role: 'user' | 'assistant' | 'system' = 'user'
    ): Promise<ChatMessage> {
        const response = await fetch(`${this.backendUrl}/v1/chat/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                content,
                role,
                metadata: {},
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to add message: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Обновление чат-сессии
     */
    async updateSession(
        sessionId: string,
        updates: {
            title?: string;
            is_active?: boolean;
            metadata?: Record<string, any>;
        }
    ): Promise<ChatSession> {
        const response = await fetch(`${this.backendUrl}/v1/chat/sessions/${sessionId}`, {
            method: 'PUT',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(updates),
        });

        if (!response.ok) {
            throw new Error(`Failed to update session: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Удаление чат-сессии
     */
    async deleteSession(sessionId: string): Promise<void> {
        const response = await fetch(`${this.backendUrl}/v1/chat/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Failed to delete session: ${response.statusText}`);
        }
    }

    /**
     * Общение с AI агентом
     */
    async chatWithAgent(
        message: string,
        sessionId?: string,
        deviceId?: string
    ): Promise<AgentChatResponse> {
        const response = await fetch(`${this.backendUrl}/v1/agent/chat`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                message,
                session_id: sessionId,
                device_id: deviceId || this.deviceId,
                metadata: {},
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to chat with agent: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Получение возможностей агента
     */
    async getAgentCapabilities(): Promise<AgentCapabilities> {
        const response = await fetch(`${this.backendUrl}/v1/agent/capabilities`, {
            headers: this.getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Failed to get agent capabilities: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Получение сообщений чата с пагинацией
     */
    async getMessages(
        sessionId: string,
        limit = 100,
        offset = 0
    ): Promise<ChatMessage[]> {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
        });

        const response = await fetch(
            `${this.backendUrl}/v1/chat/sessions/${sessionId}/messages?${params}`,
            {
                headers: this.getAuthHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to get messages: ${response.statusText}`);
        }

        return response.json();
    }
}

export const chatService = ChatService.getInstance();
