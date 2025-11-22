import { useGraphContext } from "@/contexts/GraphContext";
import { useToast } from "@/hooks/use-toast";
import { ProgrammingLanguageOptions } from "@opencanvas/shared/types";
import { ThreadPrimitive, useComposerRuntime } from "@assistant-ui/react";
import { Thread as ThreadType } from "@langchain/langgraph-sdk";
import { ArrowDownIcon, FileUp, PanelRightOpen, SquarePen } from "lucide-react";
import { Dispatch, FC, SetStateAction, useState, useEffect, useRef } from "react";
// ReflectionsDialog import removed
import { useLangSmithLinkToolUI } from "../tool-hooks/LangSmithLinkToolUI";
import { TooltipIconButton } from "../ui/assistant-ui/tooltip-icon-button";
import { TighterText } from "../ui/header";
import { Composer } from "./composer";
import { AssistantMessage, UserMessage } from "./messages";
import ModelSelector from "./model-selector";
import { ThreadHistory } from "./thread-history";
import { ThreadWelcome } from "./welcome";
import { useUserContext } from "@/contexts/UserContext";
import { useThreadContext } from "@/contexts/ThreadProvider";
import { useAssistantContext } from "@/contexts/AssistantContext";
import { Button } from "../ui/button";

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="absolute -top-8 rounded-full disabled:invisible"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

export interface ThreadProps {
  userId: string | undefined;
  hasChatStarted: boolean;
  handleQuickStart: (
    type: "text" | "code",
    language?: ProgrammingLanguageOptions
  ) => void;
  setChatStarted: Dispatch<SetStateAction<boolean>>;
  switchSelectedThreadCallback: (thread: ThreadType) => void;
  searchEnabled: boolean;
  setChatCollapsed: (c: boolean) => void;
}

export const Thread: FC<ThreadProps> = (props: ThreadProps) => {
  const {
    setChatStarted,
    hasChatStarted,
    handleQuickStart,
    switchSelectedThreadCallback,
  } = props;
  const { toast } = useToast();
  const {
    graphData: { clearState, runId, feedbackSubmitted, setFeedbackSubmitted, isStreaming },
  } = useGraphContext();
  const { selectedAssistant } = useAssistantContext();
  const {
    modelName,
    setModelName,
    modelConfig,
    setModelConfig,
    modelConfigs,
    setThreadId,
  } = useThreadContext();
  const { user } = useUserContext();
  const [isDocumentUploaded, setIsDocumentUploaded] = useState(false);
  const composerRuntime = useComposerRuntime();
  const uploadedFileRef = useRef<File | null>(null);

  // Effect to handle reattaching document after messages
  useEffect(() => {
    // Only try to reattach when streaming is done and we have an uploaded file
    if (!isStreaming && uploadedFileRef.current && composerRuntime) {
      // Small delay to ensure composer is ready after streaming completes
      const timeoutId = setTimeout(() => {
        if (uploadedFileRef.current && composerRuntime) {
          composerRuntime.addAttachment(uploadedFileRef.current);
        }
      }, 500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [isStreaming, composerRuntime]);

  // Render the LangSmith trace link
  useLangSmithLinkToolUI();

  const handleNewSession = async () => {
    if (!user) {
      toast({
        title: "User not found",
        description: "Failed to create thread without user",
        duration: 5000,
        variant: "destructive",
      });
      return;
    }

    // Remove the threadId param from the URL
    setThreadId(null);

    setModelName(modelName);
    setModelConfig(modelName, modelConfig);
    clearState();
    setChatStarted(false);
    setIsDocumentUploaded(false);
    uploadedFileRef.current = null;
  };

  const handleDocumentUpload = (event: any = null) => {
    // If an event with files is provided, use it directly
    if (event && event.target && event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      processUploadedFile(file);
    } else {
      // Otherwise create a file input and trigger click for manual selection
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.pdf,.docx,.txt';
      input.onchange = (e: any) => {
        const file = e.target.files[0];
        if (file) {
          processUploadedFile(file);
        }
      };
      input.click();
    }
  };

  const processUploadedFile = (file: File) => {
    // Store the file for later reattachment
    uploadedFileRef.current = file;
    
    toast({
      title: "Document Upload",
      description: "Uploading and indexing your document...",
      duration: 2000,
    });
    
    // Here you would connect to your backend API
    // This is a placeholder that simulates successful upload
    setTimeout(() => {
      setIsDocumentUploaded(true);
      // Ensure the file is attached to the composer
      if (composerRuntime) {
        composerRuntime.addAttachment(file);
      }
      
      toast({
        title: "Document Indexed",
        description: "Document successfully indexed. You can now ask questions.",
        duration: 3000,
      });
    }, 2000);
    
    // For actual implementation, you'd use fetch or axios:
    /*
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify({
      title: file.name,
      author: "User"
    }));
    
    try {
      const response = await fetch('http://localhost:5001/index/document/', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      // Handle task_id and polling here
      
      setIsDocumentUploaded(true);
    } catch (error) {
      console.error('Error uploading document:', error);
      toast({
        title: "Upload Failed",
        description: "Failed to upload document. Please try again.",
        duration: 5000,
        variant: "destructive",
      });
    }
    */
  };

  return (
    <ThreadPrimitive.Root className="flex flex-col h-full w-full relative pb-10">
      <div className="pr-3 pl-6 pt-3 pb-2 flex flex-row gap-4 items-center justify-between bg-neutral-50 border-b border-neutral-200">
        <div className="flex items-center justify-start gap-2 text-gray-600">
          <ThreadHistory
            switchSelectedThreadCallback={switchSelectedThreadCallback}
          />
          {false && !hasChatStarted && (
            <ModelSelector
              modelName={modelName}
              setModelName={setModelName}
              modelConfig={modelConfig}
              setModelConfig={setModelConfig}
              modelConfigs={modelConfigs}
            />
          )}
        </div>
        {hasChatStarted ? (
          <div className="flex flex-row flex-1 gap-2 items-center justify-end">
            <TooltipIconButton
              tooltip="Collapse Chat"
              variant="ghost"
              className="w-8 h-8"
              delayDuration={400}
              onClick={() => props.setChatCollapsed(true)}
            >
              <PanelRightOpen className="text-gray-600" />
            </TooltipIconButton>
            <TooltipIconButton
              tooltip="New chat"
              variant="ghost"
              className="w-8 h-8"
              delayDuration={400}
              onClick={handleNewSession}
            >
              <SquarePen className="text-gray-600" />
            </TooltipIconButton>
          </div>
        ) : (
          <div className="flex flex-row gap-2 items-center">
            {/* Upload document button also removed from here */}
          </div>
        )}
      </div>
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto scroll-smooth bg-inherit px-4 pt-8">
        {!hasChatStarted && (
          <ThreadWelcome
            handleQuickStart={handleQuickStart}
            composer={
              <Composer
                chatStarted={false}
                userId={props.userId}
                searchEnabled={props.searchEnabled}
                isDocumentUploaded={isDocumentUploaded}
              />
            }
            searchEnabled={props.searchEnabled}
            handleDocumentUpload={handleDocumentUpload}
            isDocumentUploaded={isDocumentUploaded}
          />
        )}
        <ThreadPrimitive.Messages
          components={{
            UserMessage: UserMessage,
            AssistantMessage: (prop) => (
              <AssistantMessage
                {...prop}
                feedbackSubmitted={feedbackSubmitted}
                setFeedbackSubmitted={setFeedbackSubmitted}
                runId={runId}
              />
            ),
          }}
        />
      </ThreadPrimitive.Viewport>
      <div className="mt-4 flex w-full flex-col items-center justify-end rounded-t-lg bg-inherit pb-4 px-4">
        <ThreadScrollToBottom />
        <div className="w-full max-w-2xl">
          {hasChatStarted && (
            <div className="flex flex-col space-y-2">
              {false && (
                <ModelSelector
                  modelName={modelName}
                  setModelName={setModelName}
                  modelConfig={modelConfig}
                  setModelConfig={setModelConfig}
                  modelConfigs={modelConfigs}
                />
              )}
              <Composer
                chatStarted={true}
                userId={props.userId}
                searchEnabled={props.searchEnabled}
                isDocumentUploaded={isDocumentUploaded}
              />
            </div>
          )}
        </div>
      </div>
      {/* <div className="fixed bottom-0 left-0 right-0 text-center text-xs text-gray-500 py-2 border-t border-gray-200 bg-white z-10">
        © 2025 PAKTON | Powered by Raptopoulos Petros | petrosrapto@gmail.com
      </div> */}
      <div className="fixed bottom-0 left-0 right-0 text-center text-xs text-gray-500 py-2 border-t border-gray-200 bg-white z-10">
        © 2025 PAKTON - Made by <a href="https://petrosraptopoulos.com/" target="_blank" rel="noopener noreferrer" className="hover:text-gray-700 underline">Petros Raptopoulos</a>
      </div>
    </ThreadPrimitive.Root>
  );
};
