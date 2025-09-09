"use client";

import React, { useState, useEffect } from "react";
import { Bot } from "lucide-react";
import TextType from "./TextType";

interface AnimatedMessageProps {
  author: string;
  text: string;
  time?: string;
  delay?: number;
  onComplete?: () => void;
  typingSpeed?: number;
  showActions?: boolean;
  actions?: Array<{
    icon?: React.ReactNode;
    text: string;
    delay?: number;
  }>;
}

const AnimatedMessage = ({
  author,
  text,
  time,
  delay = 0,
  onComplete,
  typingSpeed = 75,
  showActions = false,
  actions = [],
}: AnimatedMessageProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showActionsNow, setShowActionsNow] = useState(false);
  const [isTypingComplete, setIsTypingComplete] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  const handleTextComplete = () => {
    setIsTypingComplete(true);
    
    if (showActions && actions.length > 0) {
      setTimeout(() => {
        setShowActionsNow(true);
        // Вызываем onComplete после показа действий
        if (onComplete) {
          setTimeout(onComplete, 1500);
        }
      }, 500);
    } else {
      // Если нет действий, вызываем onComplete сразу
      if (onComplete) {
        setTimeout(onComplete, 800);
      }
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`flex gap-4 transition-all duration-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
      <div className="h-10 w-10 rounded-full bg-neutral-200 flex items-center justify-center text-neutral-600 shrink-0">
        <Bot size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="mb-2 font-medium text-neutral-800" style={{fontSize: '17px'}}>{author}</div>
        <div className="rounded-xl border border-neutral-200 bg-white px-5 py-4 text-neutral-800" style={{fontSize: '16px', lineHeight: '1.6'}}>
          <TextType 
            text={text}
            typingSpeed={typingSpeed}
            showCursor={!isTypingComplete}
            cursorCharacter="|"
            loop={false}
            onSentenceComplete={handleTextComplete}
            className="text-neutral-800"
            style={{ color: '#262626' }}
          />
          
          {showActionsNow && actions.map((action, index) => (
            <div 
              key={index}
              className="mt-4 inline-flex items-center gap-3 rounded-lg border border-neutral-200 bg-white px-4 py-2 text-neutral-700 animate-fadeIn" 
              style={{fontSize: '15px', animationDelay: `${(action.delay || 0) + index * 200}ms`}}
            >
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-neutral-400" />
              {action.text}
              {action.icon}
            </div>
          ))}
        </div>
      </div>
      {time && (
        <div className="w-32 shrink-0 text-right text-neutral-500 self-end" style={{fontSize: '14px'}}>
          {time}
        </div>
      )}
    </div>
  );
};

export default AnimatedMessage;
