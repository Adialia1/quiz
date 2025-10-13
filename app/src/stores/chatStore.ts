/**
 * Chat Store - Zustand store for AI Mentor chat
 * Manages conversations and messages
 */
import { create } from 'zustand';
import { ChatMessage, ChatConversation } from '../utils/aiChatApi';

interface ChatState {
  // Current conversation
  currentConversation: ChatConversation | null;
  messages: ChatMessage[];

  // All conversations
  conversations: ChatConversation[];

  // Loading states
  isLoadingMessages: boolean;
  isLoadingConversations: boolean;
  isSendingMessage: boolean;

  // Actions
  setCurrentConversation: (conversation: ChatConversation | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setConversations: (conversations: ChatConversation[]) => void;
  updateConversation: (conversationId: string, updates: Partial<ChatConversation>) => void;
  deleteConversationFromStore: (conversationId: string) => void;
  setLoadingMessages: (loading: boolean) => void;
  setLoadingConversations: (loading: boolean) => void;
  setSendingMessage: (loading: boolean) => void;
  clearCurrentChat: () => void;
  reset: () => void;
}

/**
 * Chat Store
 */
export const useChatStore = create<ChatState>((set) => ({
  // Initial state
  currentConversation: null,
  messages: [],
  conversations: [],
  isLoadingMessages: false,
  isLoadingConversations: false,
  isSendingMessage: false,

  // Actions
  setCurrentConversation: (conversation) =>
    set({ currentConversation: conversation }),

  setMessages: (messages) =>
    set({ messages }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  setConversations: (conversations) =>
    set({ conversations }),

  updateConversation: (conversationId, updates) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId ? { ...conv, ...updates } : conv
      ),
      currentConversation:
        state.currentConversation?.id === conversationId
          ? { ...state.currentConversation, ...updates }
          : state.currentConversation,
    })),

  deleteConversationFromStore: (conversationId) =>
    set((state) => ({
      conversations: state.conversations.filter(
        (conv) => conv.id !== conversationId
      ),
      currentConversation:
        state.currentConversation?.id === conversationId
          ? null
          : state.currentConversation,
      messages:
        state.currentConversation?.id === conversationId ? [] : state.messages,
    })),

  setLoadingMessages: (loading) =>
    set({ isLoadingMessages: loading }),

  setLoadingConversations: (loading) =>
    set({ isLoadingConversations: loading }),

  setSendingMessage: (loading) =>
    set({ isSendingMessage: loading }),

  clearCurrentChat: () =>
    set({
      currentConversation: null,
      messages: [],
    }),

  reset: () =>
    set({
      currentConversation: null,
      messages: [],
      conversations: [],
      isLoadingMessages: false,
      isLoadingConversations: false,
      isSendingMessage: false,
    }),
}));
