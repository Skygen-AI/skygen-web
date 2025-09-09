"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { MessageCircle, Bot, Plus, Home, Settings, User, HelpCircle, Wind, BookOpen, BarChart3, Monitor } from "lucide-react";
import { AiInput } from "../../components/ui/ai-input";
import { Sidebar, SidebarBody, SidebarLink } from "../../components/ui/sidebar";
import { useChat } from "../../hooks/useChat";
import { ChatMessage, ChatConversation } from "../../types/chat";
import { ChatMessage as ChatMessageComponent } from "../../components/ChatMessage";
import { geminiService } from "../../services/geminiService";
import { ThemeToggle } from "../../components/ThemeToggle";
import { useTheme } from "../../contexts/ThemeContext";
import { Component as EtheralShadow } from "../../components/ui/etheral-shadow";


function SidebarItem(props: {
  title: string;
  subtitle: string;
  time?: string;
  active?: boolean;
  onClick?: () => void;
}) {
  const { title, subtitle, time, active, onClick } = props;
  return (
    <div
      className={
        "flex items-start gap-4 px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 border " +
        (active 
          ? "bg-neutral-100 border-neutral-300 hover:border-neutral-400 dark:bg-neutral-700 dark:border-neutral-600 dark:hover:border-neutral-500" 
          : "bg-transparent border-transparent hover:bg-neutral-50 hover:border-neutral-200 dark:hover:bg-neutral-800 dark:hover:border-neutral-700")
      }
      onClick={onClick}
    >
      <div className={`mt-1 h-11 w-11 rounded-lg flex items-center justify-center transition-colors ${
        active 
          ? "bg-white text-black dark:bg-white dark:text-black" 
          : "bg-neutral-200 text-neutral-600 dark:bg-neutral-600 dark:text-neutral-300"
      }`}>
        <MessageCircle size={20} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className={`truncate font-medium ${
            active 
              ? "text-neutral-900 dark:text-white" 
              : "text-neutral-900 dark:text-neutral-100"
          }`} style={{fontSize: '18px'}}>{title}</p>
          {time ? (
            <span className={`shrink-0 ${
              active 
                ? "text-neutral-600 dark:text-white/70" 
                : "text-neutral-500 dark:text-neutral-400"
            }`} style={{fontSize: '15px'}}>{time}</span>
          ) : null}
        </div>
        <p className={`truncate mt-1 ${
          active 
            ? "text-neutral-600 dark:text-white/80" 
            : "text-neutral-500 dark:text-neutral-400"
        }`} style={{fontSize: '16px'}}>{subtitle}</p>
      </div>
    </div>
  );
}



export default function AppPage() {
  const { theme } = useTheme();
  
  // Initialize chat system
  const {
    conversations,
    activeConversationId,
    activeConversation,
    addUserMessage,
    addAssistantMessage,
    addTypingIndicator,
    removeTypingIndicator,
    createConversation,
    setActiveConversation,
  } = useChat([
    {
      id: 'welcome-chat',
      title: 'Welcome',
      subtitle: 'Start a new conversation',
      messages: [],
      lastMessageTime: 'now',
    }
  ]);

  // Ref for auto-scroll
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isUserAtBottom, setIsUserAtBottom] = useState<boolean>(true);

  // Handle message sending
  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;
    
    // If no active conversation, create a new one
    if (!activeConversation) {
      createConversation(
        content.slice(0, 50) + (content.length > 50 ? '...' : ''),
        'New Conversation'
      );
    }
    
    // Add user message
    addUserMessage(content);
    
    // Show "typing" indicator
    addTypingIndicator();
    
    try {
      // Get message history from current conversation for context
      const conversationHistory = activeConversation?.messages || [];
      
      // Call Gemini API with context
      const response = await geminiService.sendMessageWithContext(
        content, 
        conversationHistory
      );
      
      // Remove "typing" indicator and add assistant response
      removeTypingIndicator();
      addAssistantMessage(response);
    } catch (error) {
      console.error('Error getting AI response:', error);
      // Remove "typing" indicator and show error
      removeTypingIndicator();
      addAssistantMessage('Sorry, an error occurred while contacting the AI. Please try again.');
    }
  }, [activeConversation, createConversation, addUserMessage, addAssistantMessage, addTypingIndicator, removeTypingIndicator]);

  // Data for new sidebar
  const sidebarLinks = [
    {
      label: "Blog",
      href: "#",
      icon: <BookOpen className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Settings",
      href: "/settings",
      icon: <Settings className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Dashboard",
      href: "#",
      icon: <BarChart3 className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Chats",
      href: "#",
      icon: <MessageCircle className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Devices",
      href: "/devices",
      icon: <Monitor className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    }
  ];


  // Function to check if user is at the bottom
  const checkIfUserAtBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      const threshold = 50; // Threshold in pixels to determine "close to bottom"
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - threshold;
      setIsUserAtBottom(isAtBottom);
    }
  }, []);

  // Scroll handler
  const handleScroll = useCallback(() => {
    checkIfUserAtBottom();
  }, [checkIfUserAtBottom]);



  // Set up scroll handler
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      // Check position on mount
      checkIfUserAtBottom();
      
      return () => {
        container.removeEventListener('scroll', handleScroll);
      };
    }
  }, [handleScroll, checkIfUserAtBottom]);

  // Auto-scroll to new messages (only if user is at the bottom)
  useEffect(() => {
    if (messagesContainerRef.current && activeConversation?.messages.length && isUserAtBottom) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [activeConversation?.messages.length, isUserAtBottom]);



  return (
    <div className="h-dvh w-dvw text-neutral-900 bg-neutral-900 dark:text-neutral-100 dark:bg-neutral-950">
      <div className="flex h-full">
        {/* New Sidebar */}
        <Sidebar animate={true}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
              {/* Skygen Title */}
              <SidebarLink
                link={{
                  label: "Skygen",
                  href: "#",
                  icon: <Wind className="h-6 w-6 text-neutral-200 dark:text-neutral-200 flex-shrink-0" style={{ transform: "scaleX(-1)" }} />
                }}
                className="px-2 py-4 pointer-events-none"
              />
              
              {/* Spacing after title */}
              <div className="h-6"></div>
              
              {/* Navigation Links */}
              {sidebarLinks.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
            
            {/* User Profile */}
            <div>
              <SidebarLink
                link={{
                  label: "Egor Andreevich",
                  href: "#",
                  icon: (
                    <div className="h-10 w-10 min-h-10 min-w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-base flex-shrink-0" style={{ transform: "translateX(-3px)" }}>
                      <span className="leading-none">EA</span>
                    </div>
                  )
                }}
              />
            </div>
          </SidebarBody>
        </Sidebar>

        {/* Original Chat Sidebar */}
        <aside className="w-64 lg:w-72 border-r border-neutral-200 bg-white rounded-tl-3xl rounded-bl-3xl dark:border-neutral-700 dark:bg-neutral-800">
          <div className="px-4 py-4">
            <div className="mb-4 flex items-center justify-between gap-2">
              <button 
                onClick={() => {
                  const newConvId = createConversation('New Conversation', 'Start chatting');
                }}
                className="inline-flex items-center gap-2 rounded-lg bg-neutral-900 px-4 py-2 font-medium text-white hover:opacity-95 transition-opacity dark:bg-neutral-700 dark:text-white dark:hover:bg-neutral-600" 
                style={{fontSize: '17px'}}
              >
                <Plus size={18} />
                New Task
                <span className="ml-1 rounded bg-neutral-800 px-2 py-1 dark:bg-neutral-600" style={{fontSize: '15px'}}>⌘K</span>
              </button>
            </div>
            <div className="mb-3 text-neutral-500 dark:text-neutral-400" style={{fontSize: '16px'}}>New Chat</div>
          </div>
          <div className="space-y-2 px-3 pb-4">
            {conversations.map((conversation) => (
            <SidebarItem
                key={conversation.id}
                title={conversation.title}
                subtitle={conversation.subtitle}
                time={conversation.lastMessageTime}
                active={conversation.id === activeConversationId}
                onClick={() => setActiveConversation(conversation.id)}
              />
            ))}
          </div>
        </aside>

        {/* Main */}
        <main className="flex min-w-0 flex-1 flex-col bg-[#F8F8F6] dark:bg-neutral-900 relative">
          {/* Static Background Pattern - only for light theme */}
          {theme !== 'dark' && (
            <div className="absolute inset-0 pointer-events-none z-0">
              <EtheralShadow
                color="rgba(160, 160, 160, 0.05)"
                animation={{
                  scale: 0,
                  speed: 0
                }}
                noise={{
                  opacity: 0.02,
                  scale: 0.8
                }}
                className="w-full h-full"
              />
              
              {/* Additional Noise Texture Overlay */}
              <div 
                className="absolute inset-0 pointer-events-none"
                style={{
                  backgroundImage: `url("https://framerusercontent.com/images/g0QcWrxr87K0ufOxIUFBakwYA8.png")`,
                  backgroundSize: '280px 280px',
                  backgroundRepeat: 'repeat',
                  opacity: 0.056,
                  mixBlendMode: 'overlay',
                  imageRendering: 'pixelated'
                }}
              />
            </div>
          )}
          
          {/* Header */}
          <div className="flex items-center justify-between px-5 md:px-7 py-5 relative z-10">
            <h1 className="truncate font-semibold text-neutral-900 dark:text-neutral-100" style={{fontSize: '28px'}}>
              {activeConversation?.title || 'Select a conversation'}
            </h1>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              {activeConversation && activeConversation.messages.length > 0 && (
              <div className="rounded-full bg-neutral-100 px-4 py-2 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-300" style={{fontSize: '17px'}}>
                  {activeConversation.messages.length} message{activeConversation.messages.length === 1 ? '' : 's'}
              </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div 
            ref={messagesContainerRef}
            className="flex-1 overflow-auto px-5 md:px-7 py-6 relative z-10"
          >
            <div className="mx-auto max-w-6xl space-y-7">
              {activeConversation && activeConversation.messages.length > 0 ? (
                // Display messages from active conversation
                                activeConversation.messages.map((message, index) => {
                  // Determine if this is the last real assistant message
                  const assistantMessages = activeConversation.messages.filter(m => 
                    m.author === 'assistant' && m.status !== 'typing'
                  );
                  const lastAssistantMessage = assistantMessages[assistantMessages.length - 1];
                  const isLastAssistantMessage = 
                    message.author === 'assistant' && 
                    message.status !== 'typing' &&
                    message.id === lastAssistantMessage?.id &&
                    // Only if this message was recently added (less than 5 seconds ago)
                    (Date.now() - message.timestamp.getTime()) < 5000;
                    
                    return (
                    <ChatMessageComponent 
                      key={message.id} 
                      message={message}
                      showTime={true}
                      isLatest={isLastAssistantMessage}
                    />
                  );
                })
              ) : (
                // Show placeholder if no messages
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <div className="rounded-full bg-neutral-100 p-4 mb-4 dark:bg-neutral-700">
                    <Bot size={32} className="text-neutral-400 dark:text-neutral-500" />
                  </div>
                  <h3 className="text-xl font-medium text-neutral-700 mb-2 dark:text-neutral-300">
                    Start a new conversation
                  </h3>
                  <p className="text-neutral-500 max-w-md dark:text-neutral-400">
                    Ask a question or describe a task, and I&apos;ll help you
                  </p>
                    </div>
              )}
            </div>
          </div>

          {/* Bottom bars */}
          <div className="px-5 md:px-7 py-4 relative z-10">
            <div className="mx-auto max-w-6xl">


              {/* New AI Input Component */}
              <AiInput onSendMessage={handleSendMessage} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
