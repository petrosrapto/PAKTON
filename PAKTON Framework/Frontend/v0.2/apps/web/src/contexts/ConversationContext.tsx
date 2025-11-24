import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useUserContext } from './UserContext';
import { conversationService } from '@/services/conversationService';
import { Conversation, ConversationMessage } from '@/types/conversation';
import { useToast } from '@/hooks/use-toast';

interface ConversationMessagesCache {
  [threadId: string]: {
    messages: ConversationMessage[];
    fetchedAt: number;
  };
}

interface ConversationContextType {
  conversations: Conversation[];
  loading: boolean;
  selectedConversation: Conversation | null;
  error: string | null;
  messagesCache: ConversationMessagesCache;
  loadingMessages: boolean;
  fetchConversations: () => Promise<void>;
  selectConversation: (conversation: Conversation | null) => void;
  deleteConversation: (threadId: string) => Promise<void>;
  addOrUpdateConversation: (conversation: Conversation) => void;
  refreshConversations: () => Promise<void>;
  getConversationMessages: (threadId: string) => Promise<ConversationMessage[]>;
  updateConversationMessages: (threadId: string, messages: ConversationMessage[]) => void;
  clearMessagesCache: (threadId?: string) => void;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { user } = useUserContext();
  const { toast } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [messagesCache, setMessagesCache] = useState<ConversationMessagesCache>({});
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Fetch conversations when user logs in
  useEffect(() => {
    if (user && conversations.length === 0 && !loading) {
      fetchConversations();
    }
  }, [user]);

  const fetchConversations = async () => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const fetchedConversations = await conversationService.getConversations(100, 0);
      
      // Sort conversations by updated_at in descending order (newest first)
      const sortedConversations = fetchedConversations.sort((a, b) => {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      });
      
      setConversations(sortedConversations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch conversations';
      setError(errorMessage);
      console.error('Error fetching conversations:', err);
      
      // Only show toast for unexpected errors, not auth issues
      if (!errorMessage.includes('Authentication')) {
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive',
          duration: 5000,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const refreshConversations = async () => {
    // Force refresh by clearing current conversations first
    await fetchConversations();
  };

  const selectConversation = (conversation: Conversation | null) => {
    setSelectedConversation(conversation);
  };

  const deleteConversation = async (threadId: string) => {
    try {
      await conversationService.deleteConversation(threadId);
      
      // Remove from local state
      setConversations(prev => prev.filter(conv => conv.thread_id !== threadId));
      
      // Clear message cache for this conversation
      clearMessagesCache(threadId);
      
      // Clear selection if this conversation was selected
      if (selectedConversation?.thread_id === threadId) {
        setSelectedConversation(null);
      }
      
      toast({
        title: '✅ Conversation deleted',
        description: 'Conversation deleted successfully',
        duration: 3000,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete conversation';
      console.error('Error deleting conversation:', err);
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
        duration: 5000,
      });
      
      throw err;
    }
  };

  const addOrUpdateConversation = (conversation: Conversation) => {
    setConversations(prev => {
      const existingIndex = prev.findIndex(conv => conv.thread_id === conversation.thread_id);
      
      if (existingIndex >= 0) {
        // Update existing conversation
        const updated = [...prev];
        updated[existingIndex] = conversation;
        
        // Re-sort after update
        return updated.sort((a, b) => {
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
      } else {
        // Add new conversation
        const newConversations = [conversation, ...prev];
        
        // Sort by updated_at
        return newConversations.sort((a, b) => {
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
      }
    });
  };

  const getConversationMessages = async (threadId: string): Promise<ConversationMessage[]> => {
    // Check if messages are already cached
    if (messagesCache[threadId]) {
      console.log(`[ConversationContext] Using cached messages for conversation ${threadId} (${messagesCache[threadId].messages.length} messages)`);
      return messagesCache[threadId].messages;
    }

    // Fetch messages from backend
    setLoadingMessages(true);
    try {
      console.log(`[ConversationContext] Fetching messages for conversation ${threadId} from backend`);
      const messages = await conversationService.getConversationMessages(threadId);
      
      // Cache the messages
      setMessagesCache(prev => ({
        ...prev,
        [threadId]: {
          messages,
          fetchedAt: Date.now(),
        },
      }));

      return messages;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch conversation messages';
      console.error('Error fetching conversation messages:', err);
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
        duration: 5000,
      });
      
      throw err;
    } finally {
      setLoadingMessages(false);
    }
  };

  const updateConversationMessages = (threadId: string, messages: ConversationMessage[]) => {
    console.log(`[ConversationContext] Updating cached messages for conversation ${threadId} with ${messages.length} messages:`, messages.map(m => ({ role: m.role, content: m.content.substring(0, 50) })));
    setMessagesCache(prev => ({
      ...prev,
      [threadId]: {
        messages,
        fetchedAt: Date.now(),
      },
    }));
  };

  const clearMessagesCache = (threadId?: string) => {
    if (threadId) {
      console.log(`Clearing message cache for conversation ${threadId}`);
      setMessagesCache(prev => {
        const newCache = { ...prev };
        delete newCache[threadId];
        return newCache;
      });
    } else {
      console.log('Clearing all message caches');
      setMessagesCache({});
    }
  };

  const contextValue: ConversationContextType = {
    conversations,
    loading,
    selectedConversation,
    error,
    messagesCache,
    loadingMessages,
    fetchConversations,
    selectConversation,
    deleteConversation,
    addOrUpdateConversation,
    refreshConversations,
    getConversationMessages,
    updateConversationMessages,
    clearMessagesCache,
  };

  return (
    <ConversationContext.Provider value={contextValue}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversationContext() {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error('useConversationContext must be used within a ConversationProvider');
  }
  return context;
}