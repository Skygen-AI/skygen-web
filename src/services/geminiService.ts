"use client";

import { ChatMessage } from "@/types/chat";

export class GeminiService {
  // Отправка сообщения с контекстом через серверный API
  async sendMessageWithContext(
    userMessage: string, 
    conversationHistory: ChatMessage[] = []
  ): Promise<string> {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          history: conversationHistory
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Ошибка сервера');
      }

      return data.response;
    } catch (error) {
      console.error('Ошибка при обращении к API:', error);
      
      if (error instanceof Error) {
        return `Ошибка: ${error.message}`;
      }
      
      return 'Произошла неизвестная ошибка при обращении к AI. Попробуйте еще раз.';
    }
  }

  // Простой запрос без контекста (для тестирования)
  async sendSimpleMessage(message: string): Promise<string> {
    return this.sendMessageWithContext(message, []);
  }
}

// Экспорт единственного экземпляра сервиса
export const geminiService = new GeminiService();
