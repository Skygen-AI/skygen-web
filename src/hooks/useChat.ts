"use client";

import { useState, useCallback } from 'react';
import { ChatMessage, ChatConversation, MessageRole } from '@/types/chat';

export function useChat(initialConversations: ChatConversation[] = []) {
  const [conversations, setConversations] = useState<ChatConversation[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    initialConversations.length > 0 ? initialConversations[0].id : null
  );

  // Получить активную беседу
  const getActiveConversation = useCallback(() => {
    return conversations.find(conv => conv.id === activeConversationId) || null;
  }, [conversations, activeConversationId]);

  // Создать новое сообщение
  const createMessage = useCallback((content: string, role: MessageRole): ChatMessage => {
    return {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content,
      author: role,
      timestamp: new Date(),
      status: role === 'user' ? 'sent' : 'sending',
    };
  }, []);

  // Добавить сообщение в активную беседу
  const addMessage = useCallback((content: string, role: MessageRole) => {
    if (!activeConversationId) return;

    const newMessage = createMessage(content, role);
    
    setConversations(prev => prev.map(conv => {
      if (conv.id === activeConversationId) {
        return {
          ...conv,
          messages: [...conv.messages, newMessage],
          lastMessageTime: new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
          }),
        };
      }
      return conv;
    }));

    return newMessage.id;
  }, [activeConversationId, createMessage]);

  // Добавить сообщение пользователя
  const addUserMessage = useCallback((content: string) => {
    return addMessage(content, 'user');
  }, [addMessage]);

  // Добавить сообщение ассистента
  const addAssistantMessage = useCallback((content: string) => {
    return addMessage(content, 'assistant');
  }, [addMessage]);

  // Добавить индикатор "печатает"
  const addTypingIndicator = useCallback(() => {
    if (!activeConversationId) return null;

    const typingMessage: ChatMessage = {
      id: `typing-${Date.now()}`,
      content: 'печатает...',
      author: 'assistant',
      timestamp: new Date(),
      status: 'typing',
    };
    
    setConversations(prev => prev.map(conv => {
      if (conv.id === activeConversationId) {
        return {
          ...conv,
          messages: [...conv.messages, typingMessage],
        };
      }
      return conv;
    }));

    return typingMessage.id;
  }, [activeConversationId]);

  // Удалить индикатор "печатает"
  const removeTypingIndicator = useCallback(() => {
    setConversations(prev => prev.map(conv => ({
      ...conv,
      messages: conv.messages.filter(msg => msg.status !== 'typing')
    })));
  }, []);

  // Обновить статус сообщения
  const updateMessageStatus = useCallback((messageId: string, status: ChatMessage['status']) => {
    setConversations(prev => prev.map(conv => ({
      ...conv,
      messages: conv.messages.map(msg => 
        msg.id === messageId ? { ...msg, status } : msg
      )
    })));
  }, []);

  // Создать новую беседу
  const createConversation = useCallback((title: string, subtitle?: string): string => {
    const newConversation: ChatConversation = {
      id: `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title,
      subtitle: subtitle || 'Новая беседа',
      messages: [],
    };

    setConversations(prev => [newConversation, ...prev]);
    setActiveConversationId(newConversation.id);
    
    return newConversation.id;
  }, []);

  // Переключить активную беседу
  const setActiveConversation = useCallback((conversationId: string) => {
    setActiveConversationId(conversationId);
  }, []);

  // Удалить беседу
  const deleteConversation = useCallback((conversationId: string) => {
    setConversations(prev => {
      const updated = prev.filter(conv => conv.id !== conversationId);
      
      // Если удаляем активную беседу, переключаемся на первую доступную
      if (conversationId === activeConversationId) {
        setActiveConversationId(updated.length > 0 ? updated[0].id : null);
      }
      
      return updated;
    });
  }, [activeConversationId]);

  return {
    conversations,
    activeConversationId,
    activeConversation: getActiveConversation(),
    addUserMessage,
    addAssistantMessage,
    addTypingIndicator,
    removeTypingIndicator,
    updateMessageStatus,
    createConversation,
    setActiveConversation,
    deleteConversation,
  };
}
