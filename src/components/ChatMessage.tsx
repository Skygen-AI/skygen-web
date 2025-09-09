"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Bot, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatMessage as ChatMessageType } from "@/types/chat";
import TextType from "./TextType";
import { TextShimmer } from "./ui/text-shimmer";
import { ToolRenderer } from "./ToolRenderer";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { AnimatedMarkdown } from "./AnimatedMarkdown";
import { parseToolsFromMessage } from "@/utils/toolParser";

interface ChatMessageProps {
  message: ChatMessageType;
  showTime?: boolean;
  isLatest?: boolean; // Для определения, нужна ли анимация печатания
  onTypingComplete?: () => void; // Колбэк по завершению печатания
}

export function ChatMessage({ message, showTime = true, isLatest = false, onTypingComplete }: ChatMessageProps) {
  const isUser = message.author === 'user';
  const [isTypingAnimationComplete, setIsTypingAnimationComplete] = useState(!isLatest || isUser);
  const [isVisible, setIsVisible] = useState(false);
  const [hasAppeared, setHasAppeared] = useState(false);
  
  // Определяем, нужна ли анимация печатания (только для новых сообщений ассистента)
  const shouldAnimateTyping = isLatest && !isUser && message.status !== 'typing';
  
  // Парсим сообщение для извлечения инструментов
  const parsedMessage = useMemo(() => {
    if (message.status === 'typing') {
      return { textContent: '', tools: [] };
    }
    return parseToolsFromMessage(message.content);
  }, [message.content, message.status]);
  
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleTypingComplete = () => {
    setIsTypingAnimationComplete(true);
    if (onTypingComplete) {
      onTypingComplete();
    }
  };

  // Анимация появления сообщения (только для новых сообщений, не для обновлений статуса)
  useEffect(() => {
    // Если это "typing" сообщение или сообщение было только что создано
    const isNewMessage = message.status === 'typing' || 
                         (Date.now() - message.timestamp.getTime()) < 1000;
    
    if (isNewMessage && !hasAppeared) {
      const timer = setTimeout(() => {
        setIsVisible(true);
        setHasAppeared(true);
      }, 50);
      return () => clearTimeout(timer);
    } else {
      // Для старых сообщений или обновлений статуса - показываем сразу
      setIsVisible(true);
      setHasAppeared(true);
    }
  }, [message.status, hasAppeared, message.timestamp]);

  // Для старых сообщений сразу показываем без анимации печатания
  useEffect(() => {
    if (!shouldAnimateTyping) {
      setIsTypingAnimationComplete(true);
    }
  }, [shouldAnimateTyping]);

  return (
    <div className="space-y-4">
      <motion.div 
        className="flex gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: isVisible ? 1 : 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        {/* Avatar */}
        <div className="h-10 w-10 rounded-full bg-neutral-200 flex items-center justify-center text-neutral-600 shrink-0 dark:bg-neutral-600 dark:text-neutral-300">
          {isUser ? (
            <User size={20} />
          ) : (
            <Bot size={20} />
          )}
        </div>
        
        {/* Message content */}
        <div className="flex-1 min-w-0">
          <div className="mb-2 font-medium text-neutral-800 dark:text-neutral-200" style={{fontSize: '19px'}}>
            {isUser ? 'Вы' : 'skygen'}
          </div>
          <div 
            className={`rounded-xl border px-5 py-4 ${
              isUser 
                ? 'border-blue-200 bg-blue-50 text-neutral-800 dark:border-neutral-600 dark:bg-neutral-700 dark:text-white' 
                : 'border-neutral-200 bg-white text-neutral-800 dark:border-neutral-600 dark:bg-neutral-600 dark:text-white'
            }`} 
            style={{fontSize: '18px', lineHeight: '1.6'}}
          >
            {message.status === 'typing' ? (
              // Анимация "Thinking" с новым переливающимся эффектом
              <TextShimmer 
                duration={1.5}
                spread={3}
                className="text-base"
              >
                Thinking
              </TextShimmer>
                         ) : isUser || isTypingAnimationComplete || !shouldAnimateTyping ? (
               // Обычный Markdown для пользователя или завершенных сообщений
               <div className="text-neutral-800 dark:text-white">
                 <MarkdownRenderer 
                   content={parsedMessage.textContent || message.content}
                 />
               </div>
             ) : (
               // Анимация печатания Markdown для новых сообщений ассистента
               <AnimatedMarkdown 
                 text={parsedMessage.textContent || message.content}
                 typingSpeed={5}
                 onComplete={handleTypingComplete}
                 className="text-neutral-800 dark:text-white"
               />
             )}
          
          {/* Status indicator for user messages */}
          {isUser && message.status === 'sending' && (
            <div className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
              Отправляется...
            </div>
          )}
          {isUser && message.status === 'error' && (
            <div className="mt-2 text-xs text-red-500 dark:text-red-400">
              Ошибка отправки
            </div>
          )}

                     {/* Tool components inside AI message */}
           {!isUser && message.status !== 'typing' && (
             <ToolRenderer 
               tools={parsedMessage.tools}
               isTypingComplete={isTypingAnimationComplete}
             />
           )}
        </div>
        </div>
        
        {/* Timestamp */}
        {showTime && (
          <div className="w-32 shrink-0 text-right text-neutral-500 self-end dark:text-neutral-400" style={{fontSize: '16px'}}>
            {formatTime(message.timestamp)}
          </div>
        )}
      </motion.div>

    </div>
  );
}
