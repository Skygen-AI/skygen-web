export interface ChatMessage {
  id: string;
  content: string;
  author: 'user' | 'assistant';
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error' | 'typing';
}

export interface ChatConversation {
  id: string;
  title: string;
  subtitle: string;
  messages: ChatMessage[];
  lastMessageTime?: string;
  isActive?: boolean;
}

export type MessageRole = 'user' | 'assistant';
