export interface Conversation {
  thread_id: string;
  user_email: string;
  title: string | null;
  message_count: number;
  last_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationToolCall {
  name: string;
  args: Record<string, any>;
  id: string;
}

export interface ConversationTimelineItem {
  messageType: 'ai' | 'tool';
  content: string;
  toolCalls?: ConversationToolCall[];
  toolCallId?: string;
  name?: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timelineItems?: ConversationTimelineItem[];
}

export interface ConversationMessagesData {
  thread_id: string;
  messages: ConversationMessage[];
}

export interface ConversationsResponse {
  statusCode: number;
  message: string;
  data: {
    conversations: Conversation[];
    total: number;
    limit: number;
    offset: number;
  };
}

export interface ConversationResponse {
  statusCode: number;
  message: string;
  data: Conversation;
}

export interface ConversationMessagesResponse {
  statusCode: number;
  message: string;
  data: ConversationMessagesData;
}

export interface DeleteConversationResponse {
  statusCode: number;
  message: string;
  data: {};
}