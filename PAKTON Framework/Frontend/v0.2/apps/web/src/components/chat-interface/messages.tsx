"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  ActionBarPrimitive,
  getExternalStoreMessage,
  MessagePrimitive,
  MessageState,
  useMessage,
} from "@assistant-ui/react";
import React, { Dispatch, SetStateAction, type FC } from "react";

import { MarkdownText } from "@/components/ui/assistant-ui/markdown-text";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { FeedbackButton } from "./feedback";
import { TighterText } from "../ui/header";
import { useFeedback } from "@/hooks/useFeedback";
import { ContextDocumentsUI } from "../tool-hooks/AttachmentsToolUI";
import { HumanMessage } from "@langchain/core/messages";
import { OC_HIDE_FROM_UI_KEY } from "@opencanvas/shared/constants";
import { Button } from "../ui/button";
import { WEB_SEARCH_RESULTS_QUERY_PARAM } from "@/constants";
import { BookOpen, FileText, Globe } from "lucide-react";
import { useQueryState } from "nuqs";
import { useUserContext } from "@/contexts/UserContext";
import { InterrogatingIndicator } from "./interrogating-indicator";

interface AssistantMessageProps {
  runId: string | undefined;
  feedbackSubmitted: boolean;
  setFeedbackSubmitted: Dispatch<SetStateAction<boolean>>;
}

const ThinkingAssistantMessageComponent = ({
  message,
}: {
  message: MessageState;
}): React.ReactElement => {
  const { id, content } = message;
  let contentText = "";
  if (typeof content === "string") {
    contentText = content;
  } else {
    const firstItem = content?.[0];
    if (firstItem?.type === "text") {
      contentText = firstItem.text;
    }
  }

  if (contentText === "") {
    return <></>;
  }

  return (
    <Accordion
      defaultValue={`accordion-${id}`}
      type="single"
      collapsible
      className="w-full"
    >
      <AccordionItem value={`accordion-${id}`}>
        <AccordionTrigger>Analysis Details</AccordionTrigger>
        <AccordionContent>{contentText}</AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};

const ThinkingAssistantMessage = React.memo(ThinkingAssistantMessageComponent);

const WebSearchMessageComponent = ({ message }: { message: MessageState }) => {
  const [_, setShowWebResultsId] = useQueryState(
    WEB_SEARCH_RESULTS_QUERY_PARAM
  );

  const handleShowWebSearchResults = () => {
    if (!message.id) {
      return;
    }

    setShowWebResultsId(message.id);
  };

  return (
    <div className="flex mx-8">
      <Button
        onClick={handleShowWebSearchResults}
        variant="secondary"
        className="bg-blue-50 hover:bg-blue-100 transition-all ease-in-out duration-200 w-full"
      >
        <BookOpen className="size-4 mr-2" />
        View Contract References
      </Button>
    </div>
  );
};

const WebSearchMessage = React.memo(WebSearchMessageComponent);

// Component to display contract sources and citations
const ContractCitation = ({ citation }: { citation: string }) => {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-md p-2 mt-2 text-sm">
      <div className="flex items-start gap-2">
        <FileText className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-medium text-blue-800">Contract Reference:</p>
          <p className="text-blue-700">{citation}</p>
        </div>
      </div>
    </div>
  );
};

export const AssistantMessage: FC<AssistantMessageProps> = ({
  runId,
  feedbackSubmitted,
  setFeedbackSubmitted,
}) => {
  const message = useMessage();
  const msg = useMessage(getExternalStoreMessage<any>);
  const externalMessage = Array.isArray(msg) ? msg[0] : msg;
  
  const { isLast } = message;
  const isThinkingMessage = message.id.startsWith("thinking-");
  const isWebSearchMessage = message.id.startsWith("web-search-results-");

  if (isThinkingMessage) {
    return <ThinkingAssistantMessage message={message} />;
  }

  if (isWebSearchMessage) {
    return <WebSearchMessage message={message} />;
  }

  // Extract interrogation calls, intermediate content, and streaming state from additional_kwargs
  const interrogationCalls = externalMessage?.additional_kwargs?.interrogationCalls || [];
  const intermediateContent = externalMessage?.additional_kwargs?.intermediateContent || '';
  const isStreaming = externalMessage?.additional_kwargs?.streaming || false;

  return (
    <MessagePrimitive.Root className="relative grid w-[90%] grid-cols-[auto_auto_1fr] grid-rows-[auto_1fr] py-4">
      <Avatar className="col-start-1 row-span-full row-start-1 mr-4 bg-blue-100">
        <AvatarFallback className="text-blue-800">🧑‍💼</AvatarFallback>
      </Avatar>

      <div className="text-foreground col-span-2 col-start-2 row-start-1 my-1.5 break-words leading-7">
        {/* Show intermediate AI content before interrogation */}
        {intermediateContent && (
          <div className="mb-4 prose dark:prose-invert max-w-none">
            {intermediateContent}
          </div>
        )}
        
        {/* Show interrogating indicator only after intermediate content finishes streaming */}
        {interrogationCalls && interrogationCalls.length > 0 && 
          interrogationCalls
            .filter((call: any) => call.showIndicator)
            .map((call: any, index: number) => (
              <InterrogatingIndicator 
                key={index}
                toolCall={{
                  name: 'interrogation',
                  arguments: call.arguments
                }}
                isActive={call.isActive}
              />
            ))
        }
        
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
        
        {isLast && runId && (
          <MessagePrimitive.If lastOrHover assistant>
            <AssistantMessageBar
              feedbackSubmitted={feedbackSubmitted}
              setFeedbackSubmitted={setFeedbackSubmitted}
              runId={runId}
            />
          </MessagePrimitive.If>
        )}
      </div>
    </MessagePrimitive.Root>
  );
};

export const UserMessage: FC = () => {
  const msg = useMessage(getExternalStoreMessage<HumanMessage>);
  const humanMessage = Array.isArray(msg) ? msg[0] : msg;
  const { user } = useUserContext();

  if (humanMessage?.additional_kwargs?.[OC_HIDE_FROM_UI_KEY]) return null;

  const userMetadata = (user?.user_metadata ?? {}) as Record<string, unknown>;
  const metadataName = typeof userMetadata.full_name === "string" ? userMetadata.full_name : undefined;
  const metadataAvatar = typeof userMetadata.avatar_url === "string" ? userMetadata.avatar_url : undefined;

  const additionalKwargs = (humanMessage?.additional_kwargs ?? {}) as Record<string, unknown>;
  const messageAvatar = typeof additionalKwargs.avatar_url === "string" ? additionalKwargs.avatar_url : undefined;
  const messageName = typeof additionalKwargs.display_name === "string" ? additionalKwargs.display_name : undefined;

  const avatarUrl = metadataAvatar ?? messageAvatar ?? undefined;
  const displayName = metadataName ?? messageName ?? user?.email ?? "You";
  const fallbackInitial = displayName.charAt(0)?.toUpperCase() ?? "Y";

  return (
    <MessagePrimitive.Root className="flex w-[90%] flex-col items-end gap-2 py-4">
      <ContextDocumentsUI
        message={humanMessage}
        className="justify-self-end"
      />
      <div className="flex items-end gap-3 w-full justify-end">
        <div className="bg-muted text-foreground max-w-[85%] break-words rounded-3xl px-5 py-2.5">
          <MessagePrimitive.Content />
        </div>
        <Avatar className="bg-muted flex-shrink-0">
          {avatarUrl ? (
            <AvatarImage src={avatarUrl} alt={displayName} />
          ) : null}
          <AvatarFallback className="font-medium text-muted-foreground">
            {fallbackInitial}
          </AvatarFallback>
        </Avatar>
      </div>
    </MessagePrimitive.Root>
  );
};

interface AssistantMessageBarProps {
  runId: string;
  feedbackSubmitted: boolean;
  setFeedbackSubmitted: Dispatch<SetStateAction<boolean>>;
}

const AssistantMessageBarComponent = ({
  runId,
  feedbackSubmitted,
  setFeedbackSubmitted,
}: AssistantMessageBarProps) => {
  const { isLoading, sendFeedback } = useFeedback();
  
  // Return empty fragment to hide feedback buttons while preserving code
  return <></>;
  
  // Original code preserved but not executed
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="flex items-center mt-2"
    >
      {/* ...existing code... */}
    </ActionBarPrimitive.Root>
  );
};

const AssistantMessageBar = React.memo(AssistantMessageBarComponent);
