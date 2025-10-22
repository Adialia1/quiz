/**
 * AI Chat API utility functions
 * API calls for AI Mentor chat functionality
 */

import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://quiz-production-d042.up.railway.app';

/**
 * Get auth token - must be called from React component
 * Import useAuth from @clerk/clerk-expo in your component
 */
type GetTokenFn = () => Promise<string | null>;

/**
 * Chat message interface
 */
export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: string[];
}

/**
 * Chat conversation interface
 */
export interface ChatConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

/**
 * Send message request
 */
export interface SendMessageRequest {
  message: string;
  conversation_id?: string;
  include_sources?: boolean;
}

/**
 * Send message response
 */
export interface SendMessageResponse {
  message: ChatMessage;
  conversation_id: string;
  conversation_title?: string;
}

/**
 * AI Chat API functions
 */
export const aiChatApi = {
  /**
   * Send a message to AI Mentor
   */
  async sendMessage(
    data: SendMessageRequest,
    getToken: GetTokenFn
  ): Promise<SendMessageResponse> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/chat/send`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
  },

  /**
   * Get all conversations for the user
   */
  async getConversations(getToken: GetTokenFn): Promise<ChatConversation[]> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/chat/conversations`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get conversations');
    }

    return response.json();
  },

  /**
   * Get messages for a specific conversation
   */
  async getConversationMessages(
    conversationId: string,
    getToken: GetTokenFn
  ): Promise<ChatMessage[]> {
    const token = await getToken();

    const response = await fetch(
      `${API_URL}/api/chat/conversations/${conversationId}/messages`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get messages');
    }

    return response.json();
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(
    conversationId: string,
    getToken: GetTokenFn
  ): Promise<void> {
    const token = await getToken();

    const response = await fetch(
      `${API_URL}/api/chat/conversations/${conversationId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete conversation');
    }
  },

  /**
   * Rename a conversation
   */
  async renameConversation(
    conversationId: string,
    newTitle: string,
    getToken: GetTokenFn
  ): Promise<void> {
    const token = await getToken();

    const response = await fetch(
      `${API_URL}/api/chat/conversations/${conversationId}/rename`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to rename conversation');
    }
  },
};
