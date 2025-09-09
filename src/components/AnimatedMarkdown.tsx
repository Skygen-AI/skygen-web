"use client";

import React, { useState, useEffect } from 'react';
import { MarkdownRenderer } from './MarkdownRenderer';

interface AnimatedMarkdownProps {
  text: string;
  typingSpeed?: number;
  onComplete?: () => void;
  className?: string;
}

export function AnimatedMarkdown({ 
  text, 
  typingSpeed = 5, 
  onComplete,
  className = '' 
}: AnimatedMarkdownProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, typingSpeed);

      return () => clearTimeout(timer);
    } else if (currentIndex >= text.length && onComplete) {
      onComplete();
    }
  }, [currentIndex, text, typingSpeed, onComplete]);

  useEffect(() => {
    // Сбрасываем состояние при изменении текста
    setCurrentIndex(0);
    setDisplayedText('');
  }, [text]);

  return (
    <div className={className}>
      <MarkdownRenderer content={displayedText} />
      {currentIndex < text.length && (
        <span className="inline-block w-0.5 h-5 bg-neutral-800 dark:bg-neutral-200 ml-1 animate-pulse">▎</span>
      )}
    </div>
  );
}
