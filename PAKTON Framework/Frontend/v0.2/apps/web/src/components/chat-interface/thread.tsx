import { useGraphContext } from "@/contexts/GraphContext";
import { useToast } from "@/hooks/use-toast";
import { ARCHIVIST_API_URL } from "@/constants";
import { ProgrammingLanguageOptions } from "@opencanvas/shared/types";
import { ThreadPrimitive, useComposerRuntime } from "@assistant-ui/react";
import { Thread as ThreadType } from "@langchain/langgraph-sdk";
import { ArrowDownIcon, FileText, PanelRightOpen, SquarePen } from "lucide-react";
import { Dispatch, FC, SetStateAction, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
// ReflectionsDialog import removed
import { useLangSmithLinkToolUI } from "../tool-hooks/LangSmithLinkToolUI";
import { TooltipIconButton } from "../ui/assistant-ui/tooltip-icon-button";
import { Composer } from "./composer";
import { AssistantMessage, UserMessage } from "./messages";
import ModelSelector from "./model-selector";
import { ThreadHistory } from "./thread-history";
import { ThreadWelcome } from "./welcome";
import { useUserContext } from "@/contexts/UserContext";
import { useThreadContext } from "@/contexts/ThreadProvider";
import { useDocumentContext } from "@/contexts/DocumentContext";
import { DocumentPreviewDialog } from "./document-preview-dialog";
import { createSupabaseClient } from "@/lib/supabase/client";

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
  const {
    modelName,
    setModelName,
    modelConfig,
    setModelConfig,
    modelConfigs,
    setThreadId,
  } = useThreadContext();
  const { user } = useUserContext();
  const { isDocumentUploaded, setIsDocumentUploaded, uploadedFileName, setUploadedFileName, uploadedFile, setUploadedFile } = useDocumentContext();
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
    setUploadedFile(null);
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

  const pollTaskStatus = async (taskId: string, maxRetries = 30, initialInterval = 2000, backoffFactor = 1.2) => {
    const TERMINAL_STATUSES = new Set(['SUCCESS', 'FAILURE', 'REVOKED', 'IGNORED']);
    let currentInterval = initialInterval;
    
    // Get authentication token
    const supabase = createSupabaseClient();
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      throw new Error('Authentication required to check task status');
    }
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await fetch(`${ARCHIVIST_API_URL}/task_status/${taskId}`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`Status check failed: ${response.status}`);
        }

        const data = await response.json();
        const status = data.data?.task_status;

        if (TERMINAL_STATUSES.has(status)) {
          return data;
        }

        await new Promise(resolve => setTimeout(resolve, currentInterval));
        currentInterval *= backoffFactor;
      } catch (error) {
        console.error('Error polling task status:', error);
        throw error;
      }
    }

    throw new Error('Task polling timed out');
  };

  const processUploadedFile = async (file: File) => {
    const MIME_TYPES: Record<string, string> = {
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.pdf': 'application/pdf',
      '.txt': 'text/plain'
    };
    
    // Store the file for later reference
    uploadedFileRef.current = file;
    
    toast({
      title: "Document Upload",
      description: "Uploading and indexing your document...",
      duration: 2000,
    });
    
    try {
      // Get file extension
      const fileName = file.name;
      const fileExtension = '.' + fileName.split('.').pop()?.toLowerCase();
      
      // Check if file type is supported
      if (!MIME_TYPES[fileExtension]) {
        throw new Error(`Unsupported file type: ${fileExtension}. Please upload .docx, .pdf, or .txt files.`);
      }

      // Prepare form data
      const formData = new FormData();
      formData.append('file', file, fileName);
      
      const metadata = {
        title: fileName,
        author: "User"
      };
      formData.append('metadata', JSON.stringify(metadata));

      // Get authentication token
      const supabase = createSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        throw new Error('No active session. Please log in again.');
      }

      // Call index endpoint
      const response = await fetch(`${ARCHIVIST_API_URL}/index/document/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();
      const taskId = result.data?.task_id;

      if (!taskId) {
        throw new Error('No task ID returned from server');
      }

      toast({
        title: "Document Uploaded",
        description: "Processing document...",
        duration: 2000,
      });

      // Poll for task completion
      const taskResult = await pollTaskStatus(taskId);
      
      if (taskResult.data?.task_status === 'SUCCESS') {
        setIsDocumentUploaded(true);
        setUploadedFileName(file.name);
        setUploadedFile(file);
        
        toast({
          title: "✅ Document Indexed",
          description: "Document successfully indexed. You can now ask questions.",
          duration: 3000,
        });
      } else {
        throw new Error('Document indexing failed');
      }
      
    } catch (error: any) {
      console.error('Error uploading document:', error);
      toast({
        title: "Upload Failed",
        description: error.message || "Failed to upload document. Please try again.",
        duration: 5000,
        variant: "destructive",
      });
      
      // Clear the stored file on error
      uploadedFileRef.current = null;
    }
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
        <AnimatePresence mode="wait">
          {!hasChatStarted ? (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="h-full"
            >
              <ThreadWelcome
                handleQuickStart={handleQuickStart}
                composer={
                  <Composer
                    chatStarted={false}
                    userId={props.userId}
                    searchEnabled={props.searchEnabled}
                    isDocumentUploaded={isDocumentUploaded}
                    uploadedFileName={uploadedFileName}
                    uploadedFile={uploadedFile}
                  />
                }
                searchEnabled={props.searchEnabled}
                handleDocumentUpload={handleDocumentUpload}
                isDocumentUploaded={isDocumentUploaded}
              />
            </motion.div>
          ) : (
            <motion.div
              key="messages"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
            >
              {isDocumentUploaded && uploadedFileName && (
                <div className="flex justify-center mb-4">
                  <DocumentPreviewDialog 
                    file={uploadedFile || null} 
                    fileName={uploadedFileName}
                  >
                    <button className="flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-sm border border-blue-200 hover:bg-blue-100 transition-colors cursor-pointer">
                      <FileText className="h-4 w-4" />
                      <span className="font-medium">{uploadedFileName}</span>
                    </button>
                  </DocumentPreviewDialog>
                </div>
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
            </motion.div>
          )}
        </AnimatePresence>
      </ThreadPrimitive.Viewport>
      <div className="mt-4 flex w-full flex-col items-center justify-end rounded-t-lg bg-inherit pb-4 px-4">
        <ThreadScrollToBottom />
        <div className="w-[65%]">
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
                uploadedFileName={uploadedFileName}
                uploadedFile={uploadedFile}
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
