import { ARCHIVIST_API_URL } from '@/constants';
import { createSupabaseClient } from '@/lib/supabase/client';
import { 
  Conversation, 
  ConversationsResponse, 
  ConversationResponse,
  ConversationMessagesResponse,
  ConversationMessage,
  DeleteConversationResponse 
} from '@/types/conversation';

class ConversationService {
  private async getAuthToken(): Promise<string | null> {
    const supabase = createSupabaseClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  }

  private async makeAuthenticatedRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();
    
    if (!token) {
      throw new Error('Authentication required. Please log in again.');
    }

    const response = await fetch(`${ARCHIVIST_API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication expired. Please log in again.');
      }
      if (response.status === 403) {
        throw new Error('Access denied.');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Fetch all conversations for the authenticated user
   */
  async getConversations(limit: number = 50, offset: number = 0): Promise<Conversation[]> {
    try {
      const response = await this.makeAuthenticatedRequest<ConversationsResponse>(
        `/conversations?limit=${limit}&offset=${offset}`
      );
      
      if (response.statusCode !== 200) {
        throw new Error(response.message || 'Failed to fetch conversations');
      }

      return response.data.conversations;
    } catch (error) {
      console.error('Error fetching conversations:', error);
      throw error;
    }
  }

  /**
   * Fetch a specific conversation by thread_id
   */
  async getConversation(threadId: string): Promise<Conversation> {
    try {
      const response = await this.makeAuthenticatedRequest<ConversationResponse>(
        `/conversations/${threadId}`
      );
      
      if (response.statusCode !== 200) {
        throw new Error(response.message || 'Failed to fetch conversation');
      }

      return response.data;
    } catch (error) {
      console.error(`Error fetching conversation ${threadId}:`, error);
      throw error;
    }
  }

  /**
   * Fetch conversation messages by thread_id
   */
  async getConversationMessages(threadId: string): Promise<ConversationMessage[]> {
    try {
      const response = await this.makeAuthenticatedRequest<ConversationMessagesResponse>(
        `/conversations/${threadId}/messages`
      );
      
      if (response.statusCode !== 200) {
        throw new Error(response.message || 'Failed to fetch conversation messages');
      }

      return response.data.messages;
    } catch (error) {
      console.error(`Error fetching conversation messages ${threadId}:`, error);
      throw error;
    }
  }

  /**
   * Delete a conversation by thread_id
   */
  async deleteConversation(threadId: string): Promise<void> {
    try {
      const response = await this.makeAuthenticatedRequest<DeleteConversationResponse>(
        `/conversations/${threadId}`,
        { method: 'DELETE' }
      );
      
      if (response.statusCode !== 200) {
        throw new Error(response.message || 'Failed to delete conversation');
      }
    } catch (error) {
      console.error(`Error deleting conversation ${threadId}:`, error);
      throw error;
    }
  }
}

export const conversationService = new ConversationService();