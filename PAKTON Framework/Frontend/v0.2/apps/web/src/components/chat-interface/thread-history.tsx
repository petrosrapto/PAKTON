import { isToday, isYesterday, isWithinInterval, subDays } from "date-fns";
import { TooltipIconButton } from "../ui/assistant-ui/tooltip-icon-button";
import { Button } from "../ui/button";
import { Trash2, Clock, MessageCircle } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "../ui/sheet";
import { Skeleton } from "../ui/skeleton";
import { useEffect, useState } from "react";
import { Thread } from "@langchain/langgraph-sdk";
import { PiChatsCircleLight } from "react-icons/pi";
import { TighterText } from "../ui/header";
import { useGraphContext } from "@/contexts/GraphContext";
import { useToast } from "@/hooks/use-toast";
import React from "react";
import { useUserContext } from "@/contexts/UserContext";
import { useThreadContext } from "@/contexts/ThreadProvider";
import { useConversationContext } from "@/contexts/ConversationContext";
import { Conversation } from "@/types/conversation";

interface ThreadHistoryProps {
  switchSelectedThreadCallback: (thread: Thread) => void;
}

interface ConversationItemProps {
  id: string;
  onClick: () => void;
  onDelete: () => void;
  title: string;
  lastMessage: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount?: number;
}

const ConversationItem = (props: ConversationItemProps) => {
  const [isHovering, setIsHovering] = useState(false);
  
  const formatLastUpdate = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    if (diffInMinutes < 10080) return `${Math.floor(diffInMinutes / 1440)}d ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  return (
    <div
      className="group flex flex-row gap-0 items-center justify-start w-full hover:bg-gray-100 rounded-lg transition-all duration-200 hover:shadow-sm"
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <Button
        className="px-3 py-3 justify-start items-start flex-grow min-w-0 h-auto bg-transparent hover:bg-transparent"
        size="sm"
        variant="ghost"
        onClick={props.onClick}
      >
        <div className="flex flex-col items-start w-full gap-2">
          <div className="flex items-center justify-between w-full">
            <TighterText className="truncate text-sm font-semibold text-gray-900 flex-1 text-left">
              {props.title || "Untitled Conversation"}
            </TighterText>
          </div>
          
          {/* Show message count below title, or "No messages yet" for 0 messages */}
          {props.messageCount !== undefined && (
            <TighterText className="text-xs text-gray-500 w-full text-left">
              {props.messageCount === 0 ? "No messages yet" : `${props.messageCount} message${props.messageCount !== 1 ? 's' : ''}`}
            </TighterText>
          )}
          
          {/* Only show lastMessage if it exists and is not the default "No messages yet" */}
          {props.lastMessage && props.lastMessage !== "No messages yet" && (
            <TighterText className="text-xs text-gray-600 w-full text-left line-clamp-2 leading-relaxed">
              {props.lastMessage}
            </TighterText>
          )}
          
          <div className="flex items-center justify-between w-full mt-1">
            <TighterText className="text-xs text-gray-400">
              {formatLastUpdate(props.updatedAt)}
            </TighterText>
          </div>
        </div>
      </Button>
      
      <div className={`transition-opacity duration-200 ${isHovering ? 'opacity-100' : 'opacity-0'} mr-2`}>
        <TooltipIconButton
          tooltip="Delete conversation"
          variant="ghost"
          onClick={props.onDelete}
          className="h-8 w-8 text-gray-400 hover:text-black hover:bg-gray-100"
        >
          <Trash2 className="h-4 w-4" />
        </TooltipIconButton>
      </div>
    </div>
  );
};

const LoadingConversation = () => (
  <div className="px-3 py-3 space-y-2">
    <div className="flex items-center justify-between">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-12" />
    </div>
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-4/5" />
    <div className="flex items-center justify-between pt-1">
      <Skeleton className="h-3 w-16" />
    </div>
  </div>
);

const convertConversationToItemProps = (
  conversation: Conversation,
  onSelect: (conversation: Conversation) => void,
  onDelete: (threadId: string) => Promise<void>
): ConversationItemProps => ({
  id: conversation.thread_id,
  title: conversation.title || "Untitled Conversation",
  lastMessage: conversation.last_message || "No messages yet",
  createdAt: new Date(conversation.created_at),
  updatedAt: new Date(conversation.updated_at),
  messageCount: conversation.message_count,
  onClick: () => onSelect(conversation),
  onDelete: () => {
    onDelete(conversation.thread_id).catch(console.error);
  },
});

const groupConversations = (
  conversations: Conversation[],
  onSelect: (conversation: Conversation) => void,
  onDelete: (threadId: string) => Promise<void>
) => {
  const today = new Date();
  const yesterday = subDays(today, 1);
  const sevenDaysAgo = subDays(today, 7);

  return {
    today: conversations
      .filter((conv) => isToday(new Date(conv.updated_at)))
      .map((conv) => convertConversationToItemProps(conv, onSelect, onDelete)),
    yesterday: conversations
      .filter((conv) => isYesterday(new Date(conv.updated_at)))
      .map((conv) => convertConversationToItemProps(conv, onSelect, onDelete)),
    lastSevenDays: conversations
      .filter((conv) =>
        isWithinInterval(new Date(conv.updated_at), {
          start: sevenDaysAgo,
          end: yesterday,
        })
      )
      .map((conv) => convertConversationToItemProps(conv, onSelect, onDelete)),
    older: conversations
      .filter((conv) => new Date(conv.updated_at) < sevenDaysAgo)
      .map((conv) => convertConversationToItemProps(conv, onSelect, onDelete)),
  };
};

const prettifyDateLabel = (group: string): string => {
  switch (group) {
    case "today":
      return "Today";
    case "yesterday":
      return "Yesterday";
    case "lastSevenDays":
      return "This Week";
    case "older":
      return "Older";
    default:
      return group;
  }
};

const getGroupIcon = (group: string) => {
  switch (group) {
    case "today":
      return <Clock className="h-3 w-3 text-green-500" />;
    case "yesterday":
      return <Clock className="h-3 w-3 text-blue-500" />;
    case "lastSevenDays":
      return <Clock className="h-3 w-3 text-purple-500" />;
    case "older":
      return <Clock className="h-3 w-3 text-gray-500" />;
    default:
      return <Clock className="h-3 w-3 text-gray-500" />;
  }
};

interface ConversationsListProps {
  groupedConversations: {
    today: ConversationItemProps[];
    yesterday: ConversationItemProps[];
    lastSevenDays: ConversationItemProps[];
    older: ConversationItemProps[];
  };
}

function ConversationsList(props: ConversationsListProps) {
  return (
    <div className="flex flex-col pt-4 gap-6">
      {Object.entries(props.groupedConversations).map(([group, conversations], index) =>
        conversations.length > 0 ? (
          <div key={group} className="space-y-1">
            {index > 0 && <div className="border-t border-gray-100 mx-4 mb-4" />}
            <div className="flex items-center px-3 mb-3">
              <div className="flex items-center gap-2">
                {getGroupIcon(group)}
                <TighterText className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                  {prettifyDateLabel(group)}
                </TighterText>
              </div>
            </div>
            <div className="space-y-1 px-1">
              {conversations.map((conversation) => (
                <ConversationItem key={conversation.id} {...conversation} />
              ))}
            </div>
          </div>
        ) : null
      )}
    </div>
  );
}

export function ThreadHistoryComponent(props: ThreadHistoryProps) {
  const { toast } = useToast();
  const {
    graphData: { setMessages, switchSelectedThread },
  } = useGraphContext();
  const { setThreadId, createThread } = useThreadContext();
  const { 
    conversations, 
    loading, 
    deleteConversation, 
    selectConversation,
    getConversationMessages,
    loadingMessages,
  } = useConversationContext();
  const { user } = useUserContext();
  const [open, setOpen] = useState(false);

  const handleDeleteConversation = async (threadId: string) => {
    if (!user) {
      toast({
        title: "Failed to delete conversation",
        description: "User not found",
        duration: 5000,
        variant: "destructive",
      });
      return;
    }

    await deleteConversation(threadId);
  };

  const handleSelectConversation = async (conversation: Conversation) => {
    try {
      // Select the conversation in context
      selectConversation(conversation);
      
      // Set the thread ID to load the conversation
      setThreadId(conversation.thread_id);
      
      // Fetch messages (will use cache if available)
      const messages = await getConversationMessages(conversation.thread_id);
      
      // Convert messages to BaseMessage format for the GraphContext
      // For now, we'll create a simple conversion - you may need to adjust this based on your BaseMessage type
      const baseMessages = messages.map((msg) => {
        if (msg.role === 'user') {
          return {
            type: 'human',
            content: msg.content,
          };
        } else {
          return {
            type: 'ai',
            content: msg.content,
            // Include timeline items if needed
            ...(msg.timelineItems && { timelineItems: msg.timelineItems }),
          };
        }
      });
      
      // Set the messages in GraphContext
      setMessages(baseMessages as any);
      
      // Create a mock Thread object for compatibility with existing code
      const mockThread: Thread = {
        thread_id: conversation.thread_id,
        created_at: conversation.created_at,
        updated_at: conversation.updated_at,
        status: 'idle' as const,
        values: {
          messages: baseMessages,
        },
        interrupts: {},
        metadata: {
          thread_title: conversation.title,
        },
      };
      
      // Call the existing thread switching logic
      switchSelectedThread(mockThread);
      props.switchSelectedThreadCallback(mockThread);
      
      setOpen(false);
      
      // Show success message
      toast({
        title: "✅ Conversation Loaded",
        description: `Conversation "${conversation.title || 'conversation'}" loaded with ${messages.length} messages`,
        duration: 3000,
      });
    } catch (error) {
      console.error('Error selecting conversation:', error);
      toast({
        title: "Error",
        description: "Failed to load conversation messages",
        variant: "destructive",
        duration: 5000,
      });
    }
  };

  const groupedConversations = groupConversations(
    conversations,
    handleSelectConversation,
    handleDeleteConversation
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <TooltipIconButton
          tooltip="Chat History"
          variant="ghost"
          className="w-fit h-fit p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <PiChatsCircleLight
            className="w-6 h-6 text-gray-600 hover:text-gray-800"
            strokeWidth={8}
          />
        </TooltipIconButton>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-96 p-0 border-none bg-gradient-to-b from-gray-50 to-white shadow-xl flex flex-col"
        aria-describedby={undefined}
      >
        <SheetTitle>
          <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
            <div>
              <TighterText className="text-lg font-semibold text-gray-900">
                Chat History
              </TighterText>
              <TighterText className="text-sm text-gray-500">
                {conversations.length > 0 ? `${conversations.length} conversation${conversations.length !== 1 ? 's' : ''}` : 'No conversations'}
              </TighterText>
            </div>
          </div>
        </SheetTitle>

        <div className="flex-1 overflow-y-auto">
          {loading && !conversations.length ? (
            <div className="flex flex-col gap-3 px-4 pt-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <LoadingConversation key={`loading-conversation-${i}`} />
              ))}
            </div>
          ) : !conversations.length ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <PiChatsCircleLight className="w-8 h-8 text-gray-400" />
              </div>
              <TighterText className="text-gray-900 font-medium mb-1">No conversations yet</TighterText>
              <TighterText className="text-sm text-gray-500">Start a new conversation to see your chat history here</TighterText>
            </div>
          ) : (
            <ConversationsList groupedConversations={groupedConversations} />
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export const ThreadHistory = React.memo(ThreadHistoryComponent);
