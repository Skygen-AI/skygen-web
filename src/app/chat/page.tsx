"use client";

import React, { useState, useEffect, useRef } from 'react';
import { ChatService, ChatSession, ChatMessage, AgentChatResponse } from '@/services/chatService';
import { SkygenService } from '@/services/skygenService';
import { Button } from '@/components/ui/button';
import { Send, Plus, MessageCircle, Bot, User, Loader2, Settings } from 'lucide-react';

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [deviceId, setDeviceId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatService = ChatService.getInstance();
  const skygenService = SkygenService.getInstance();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
      loadDeviceId();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const checkAuth = () => {
    const authenticated = skygenService.isAuthenticated();
    setIsAuthenticated(authenticated);
  };

  const loadDeviceId = () => {
    const id = skygenService.getDeviceId();
    setDeviceId(id);
  };

  const loadSessions = async () => {
    try {
      const sessionList = await chatService.getSessions();
      setSessions(sessionList);
      
      if (sessionList.length > 0 && !currentSession) {
        await loadSession(sessionList[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      const session = await chatService.getSession(sessionId);
      setCurrentSession(session);
      setMessages(session.messages);
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const title = `Chat ${new Date().toLocaleString()}`;
      const session = await chatService.createSession(title, deviceId || undefined);
      setSessions(prev => [session, ...prev]);
      setCurrentSession(session);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSession) return;

    const userMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      // Отправляем сообщение агенту
      const response: AgentChatResponse = await chatService.chatWithAgent(
        userMessage,
        currentSession.id,
        deviceId || undefined
      );

      // Обновляем сообщения
      const newMessages = [response.message];
      if (response.assistant_message) {
        newMessages.push(response.assistant_message);
      }

      setMessages(prev => [...prev, ...newMessages]);

      // Если создана задача, показываем уведомление
      if (response.task_created && response.task_id) {
        console.log(`Task created: ${response.task_id}`);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Добавляем сообщение об ошибке
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        session_id: currentSession.id,
        role: 'assistant',
        content: 'Извините, произошла ошибка при отправке сообщения. Проверьте подключение к серверу.',
        created_at: new Date().toISOString(),
        metadata: { error: true },
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
            Требуется авторизация
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Для использования чата необходимо войти в систему
          </p>
          <Button onClick={() => window.location.href = '/skygen-setup'}>
            Перейти к настройке
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar с сессиями */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Skygen Chat
            </h1>
            <Button
              onClick={() => window.location.href = '/skygen-setup'}
              variant="ghost"
              size="sm"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
          
          <Button onClick={createNewSession} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Новый чат
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`p-3 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                currentSession?.id === session.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
              }`}
              onClick={() => loadSession(session.id)}
            >
              <h3 className="font-medium text-gray-900 dark:text-white truncate">
                {session.title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {session.message_count || 0} сообщений
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {new Date(session.updated_at).toLocaleDateString('ru-RU')}
              </p>
            </div>
          ))}
        </div>

        {deviceId && (
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-green-50 dark:bg-green-900/20">
            <p className="text-xs text-green-600 dark:text-green-400">
              Устройство подключено: {deviceId.slice(0, 8)}...
            </p>
          </div>
        )}
      </div>

      {/* Основная область чата */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <>
            {/* Заголовок чата */}
            <div className="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentSession.title}
              </h2>
              {currentSession.device_id && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Привязан к устройству
                </p>
              )}
            </div>

            {/* Сообщения */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'assistant' && (
                        <Bot className="h-4 w-4 mt-1 flex-shrink-0" />
                      )}
                      {message.role === 'user' && (
                        <User className="h-4 w-4 mt-1 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {formatTime(message.created_at)}
                        </p>
                        {message.task_id && (
                          <p className="text-xs opacity-70 mt-1">
                            📋 Задача: {message.task_id}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-lg px-4 py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Поле ввода */}
            <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
              <div className="flex space-x-2">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={
                    deviceId 
                      ? "Напишите команду для устройства или обычное сообщение..."
                      : "Подключите устройство для выполнения задач..."
                  }
                  className="flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  rows={1}
                  disabled={isLoading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              {!deviceId && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  ⚠️ Устройство не подключено. Задачи создаваться не будут.
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Выберите чат или создайте новый
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Начните общение с AI агентом Skygen
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
