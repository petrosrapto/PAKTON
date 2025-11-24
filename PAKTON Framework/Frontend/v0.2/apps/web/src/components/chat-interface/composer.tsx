"use client";

import { ComposerPrimitive, ThreadPrimitive } from "@assistant-ui/react";
import { type FC, useState, useEffect, useRef } from "react";

import { TooltipIconButton } from "@/components/ui/assistant-ui/tooltip-icon-button";
import { SendHorizontalIcon, FileText, X } from "lucide-react";
import { DragAndDropWrapper } from "./drag-drop-wrapper";
import { ComposerAttachments } from "../assistant-ui/attachment";
import { ComposerActionsPopOut } from "./composer-actions-popout";
import { DocumentPreviewDialog } from "./document-preview-dialog";

const PAKTON_PLACEHOLDERS = [
  "What terms are covered in this contract?",
  "Explain the liability clauses in this document",
  "What are my obligations under this agreement?",
  "Summarize the key points of this contract",
  "What are the termination conditions?",
  "Explain the intellectual property rights in this document",
  "What penalties are specified for breach of contract?",
  "What are the payment terms and conditions?",
  "Are there any restrictive covenants in this agreement?",
  "What's the duration of this contract?",
];

// Function to get a random placeholder that's different from the current one
const getRandomPaktonPlaceholder = (currentPlaceholder: string) => {
  let newPlaceholders = PAKTON_PLACEHOLDERS.filter(p => p !== currentPlaceholder);
  return newPlaceholders[Math.floor(Math.random() * newPlaceholders.length)];
};

const CircleStopIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      width="16"
      height="16"
    >
      <rect width="10" height="10" x="3" y="3" rx="2" />
    </svg>
  );
};

interface ComposerProps {
  chatStarted: boolean;
  userId: string | undefined;
  searchEnabled: boolean;
  isDocumentUploaded?: boolean;
  uploadedFileName?: string | null;
  uploadedFile?: File | null;
}

export const Composer: FC<ComposerProps> = (props: ComposerProps) => {
  const [placeholder, setPlaceholder] = useState("");
  const [displayedPlaceholder, setDisplayedPlaceholder] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const placeholderTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const streamingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize with a random placeholder
  useEffect(() => {
    const initialPlaceholder = PAKTON_PLACEHOLDERS[Math.floor(Math.random() * PAKTON_PLACEHOLDERS.length)];
    setPlaceholder(initialPlaceholder);
    setDisplayedPlaceholder("");
    setIsStreaming(true);
    
    return () => {
      if (placeholderTimeoutRef.current) clearTimeout(placeholderTimeoutRef.current);
      if (streamingIntervalRef.current) clearInterval(streamingIntervalRef.current);
    };
  }, []);

  // Handle the streaming effect for placeholders
  useEffect(() => {
    if (isStreaming) {
      let index = 0;
      
      // Clear any existing intervals
      if (streamingIntervalRef.current) {
        clearInterval(streamingIntervalRef.current);
      }
      
      // Set up new streaming interval
      streamingIntervalRef.current = setInterval(() => {
        if (index <= placeholder.length) {
          setDisplayedPlaceholder(placeholder.substring(0, index));
          index++;
        } else {
          setIsStreaming(false);
          if (streamingIntervalRef.current) {
            clearInterval(streamingIntervalRef.current);
          }
          
          // Schedule next placeholder change
          placeholderTimeoutRef.current = setTimeout(() => {
            const nextPlaceholder = getRandomPaktonPlaceholder(placeholder);
            setPlaceholder(nextPlaceholder);
            setDisplayedPlaceholder("");
            setIsStreaming(true);
          }, 5000); // Wait 5 seconds before changing to a new placeholder
        }
      }, 50); // Stream each character at 50ms intervals
    }
    
    return () => {
      if (streamingIntervalRef.current) clearInterval(streamingIntervalRef.current);
    };
  }, [isStreaming, placeholder]);

  return (
    <DragAndDropWrapper>
      <ComposerPrimitive.Root className="focus-within:border-aui-ring/20 flex flex-col w-full min-h-[64px] flex-wrap items-center justify-center border px-2.5 shadow-sm transition-colors ease-in bg-white rounded-2xl">
        {/* Document indicator badge */}
        {props.isDocumentUploaded && props.uploadedFileName && !props.chatStarted && (
          <div className="flex flex-wrap gap-2 items-start mr-auto w-full pt-2">
            <DocumentPreviewDialog 
              file={props.uploadedFile || null} 
              fileName={props.uploadedFileName}
            >
              <button className="flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-sm border border-blue-200 hover:bg-blue-100 transition-colors cursor-pointer">
                <FileText className="h-4 w-4" />
                <span className="font-medium">{props.uploadedFileName}</span>
              </button>
            </DocumentPreviewDialog>
          </div>
        )}

        <div className="flex flex-row w-full items-center justify-start my-auto">
          <div style={{ display: 'none' }}>
            <ComposerActionsPopOut
              userId={props.userId}
              chatStarted={props.chatStarted}
            />
          </div>
          <ComposerPrimitive.Input
            autoFocus
            placeholder={displayedPlaceholder}
            rows={1}
            className="placeholder:text-muted-foreground max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm outline-none focus:ring-0 disabled:cursor-not-allowed text-center placeholder:text-center"
          />
          <ThreadPrimitive.If running={false}>
            <ComposerPrimitive.Send asChild>
              <TooltipIconButton
                tooltip="Send"
                variant="default"
                className="my-2.5 size-8 p-2 transition-opacity ease-in"
              >
                <SendHorizontalIcon />
              </TooltipIconButton>
            </ComposerPrimitive.Send>
          </ThreadPrimitive.If>
          <ThreadPrimitive.If running>
            <ComposerPrimitive.Cancel asChild>
              <TooltipIconButton
                tooltip="Cancel"
                variant="default"
                className="my-2.5 size-8 p-2 transition-opacity ease-in"
              >
                <CircleStopIcon />
              </TooltipIconButton>
            </ComposerPrimitive.Cancel>
          </ThreadPrimitive.If>
        </div>
      </ComposerPrimitive.Root>
    </DragAndDropWrapper>
  );
};
