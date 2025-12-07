import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import { ArtifactMarkdownV3 } from "@opencanvas/shared/types";
import "@blocknote/core/fonts/inter.css";
import {
  getDefaultReactSlashMenuItems,
  SuggestionMenuController,
  useCreateBlockNote,
} from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { isArtifactMarkdownContent } from "@opencanvas/shared/utils/artifacts";
import { CopyText } from "./components/CopyText";
import { getArtifactContent } from "@opencanvas/shared/utils/artifacts";
import { useGraphContext } from "@/contexts/GraphContext";
import React from "react";
import { TooltipIconButton } from "../ui/assistant-ui/tooltip-icon-button";
import { Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";
import { Textarea } from "../ui/textarea";
import { cn } from "@/lib/utils";

const cleanText = (text: string) => {
  return text.replaceAll("\\\n", "\n");
};

function ViewRawText({
  isRawView,
  setIsRawView,
}: {
  isRawView: boolean;
  setIsRawView: Dispatch<SetStateAction<boolean>>;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <TooltipIconButton
        tooltip={`View ${isRawView ? "rendered" : "raw"} markdown`}
        variant="outline"
        delayDuration={400}
        onClick={() => setIsRawView((p) => !p)}
      >
        {isRawView ? (
          <EyeOff className="w-5 h-5 text-gray-600" />
        ) : (
          <Eye className="w-5 h-5 text-gray-600" />
        )}
      </TooltipIconButton>
    </motion.div>
  );
}

export interface TextRendererProps {
  isEditing: boolean;
  isHovering: boolean;
  isInputVisible: boolean;
}

export function TextRendererComponent(props: TextRendererProps) {
  const editor = useCreateBlockNote({});
  const { graphData } = useGraphContext();
  const {
    artifact,
    isStreaming,
    updateRenderedArtifactRequired,
    firstTokenReceived,
    setArtifact,
    setSelectedBlocks,
    setUpdateRenderedArtifactRequired,
  } = graphData;

  const [rawMarkdown, setRawMarkdown] = useState("");
  const [isRawView, setIsRawView] = useState(false);
  const [manuallyUpdatingArtifact, setManuallyUpdatingArtifact] =
    useState(false);

  useEffect(() => {
    const selectedText = editor.getSelectedText();
    const selection = editor.getSelection();

    if (selectedText && selection) {
      if (!artifact) {
        console.error("Artifact not found");
        return;
      }

      const currentBlockIdx = artifact.currentIndex;
      const currentContent = artifact.contents.find(
        (c) => c.index === currentBlockIdx
      );
      if (!currentContent) {
        console.error("Current content not found");
        return;
      }
      if (!isArtifactMarkdownContent(currentContent)) {
        console.error("Current content is not markdown");
        return;
      }

      (async () => {
        const [markdownBlock, fullMarkdown] = await Promise.all([
          editor.blocksToMarkdownLossy(selection.blocks),
          editor.blocksToMarkdownLossy(editor.document),
        ]);
        setSelectedBlocks({
          fullMarkdown: cleanText(fullMarkdown),
          markdownBlock: cleanText(markdownBlock),
          selectedText: cleanText(selectedText),
        });
      })();
    }
  }, [editor.getSelectedText()]);

  useEffect(() => {
    if (!props.isInputVisible) {
      setSelectedBlocks(undefined);
    }
  }, [props.isInputVisible]);

  // Ref to track ongoing markdown parsing to prevent race conditions
  const parsingRef = useRef(false);
  const pendingContentRef = useRef<string | null>(null);

  useEffect(() => {
    if (!artifact) {
      return;
    }
    if (
      !isStreaming &&
      !manuallyUpdatingArtifact &&
      !updateRenderedArtifactRequired
    ) {
      return;
    }

    const currentIndex = artifact.currentIndex;
    const currentContent = artifact.contents.find(
      (c) => c.index === currentIndex && c.type === "text"
    ) as ArtifactMarkdownV3 | undefined;
    if (!currentContent) return;

    const markdownContent = currentContent.fullMarkdown;
    
    // During streaming, update pending content and schedule processing
    if (isStreaming) {
      pendingContentRef.current = markdownContent;
      
      // If not currently parsing, start processing
      if (!parsingRef.current) {
        const processContent = async () => {
          while (pendingContentRef.current !== null) {
            const contentToProcess = pendingContentRef.current;
            pendingContentRef.current = null;
            parsingRef.current = true;
            
            try {
              const markdownAsBlocks = await editor.tryParseMarkdownToBlocks(contentToProcess);
              editor.replaceBlocks(editor.document, markdownAsBlocks);
            } catch (error) {
              console.error('Error parsing markdown during streaming:', error);
            }
            
            // Small delay to allow batching of rapid updates
            await new Promise(resolve => setTimeout(resolve, 50));
          }
          parsingRef.current = false;
        };
        processContent();
      }
    } else {
      // Not streaming - final update, wait for completion
      (async () => {
        parsingRef.current = true;
        try {
          const markdownAsBlocks = await editor.tryParseMarkdownToBlocks(markdownContent);
          editor.replaceBlocks(editor.document, markdownAsBlocks);
        } finally {
          parsingRef.current = false;
          setUpdateRenderedArtifactRequired(false);
          setManuallyUpdatingArtifact(false);
        }
      })();
    }
  }, [artifact, updateRenderedArtifactRequired, isStreaming]);

  useEffect(() => {
    if (isRawView) {
      editor.blocksToMarkdownLossy(editor.document).then(setRawMarkdown);
    } else if (!isRawView && rawMarkdown) {
      try {
        (async () => {
          setManuallyUpdatingArtifact(true);
          const markdownAsBlocks =
            await editor.tryParseMarkdownToBlocks(rawMarkdown);
          editor.replaceBlocks(editor.document, markdownAsBlocks);
          setManuallyUpdatingArtifact(false);
        })();
      } catch (_) {
        setManuallyUpdatingArtifact(false);
      }
    }
  }, [isRawView, editor]);

  const isComposition = useRef(false);

  const onChange = async () => {
    if (
      isStreaming ||
      manuallyUpdatingArtifact ||
      updateRenderedArtifactRequired
    )
      return;

    const fullMarkdown = await editor.blocksToMarkdownLossy(editor.document);
    setArtifact((prev) => {
      if (!prev) {
        return {
          currentIndex: 1,
          contents: [
            {
              index: 1,
              fullMarkdown: fullMarkdown,
              title: "Untitled",
              type: "text",
            },
          ],
        };
      } else {
        return {
          ...prev,
          contents: prev.contents.map((c) => {
            if (c.index === prev.currentIndex) {
              return {
                ...c,
                fullMarkdown: fullMarkdown,
              };
            }
            return c;
          }),
        };
      }
    });
  };

  const onChangeRawMarkdown = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newRawMarkdown = e.target.value;
    setRawMarkdown(newRawMarkdown);
    setArtifact((prev) => {
      if (!prev) {
        return {
          currentIndex: 1,
          contents: [
            {
              index: 1,
              fullMarkdown: newRawMarkdown,
              title: "Untitled",
              type: "text",
            },
          ],
        };
      } else {
        return {
          ...prev,
          contents: prev.contents.map((c) => {
            if (c.index === prev.currentIndex) {
              return {
                ...c,
                fullMarkdown: newRawMarkdown,
              };
            }
            return c;
          }),
        };
      }
    });
  };

  return (
    <div className="w-full h-full mt-2 flex flex-col border-t-[1px] border-gray-200 overflow-y-auto py-5 relative">
      {props.isHovering && artifact && (
        <div className="absolute flex gap-2 top-2 right-4 z-10">
          <CopyText currentArtifactContent={getArtifactContent(artifact)} />
          <ViewRawText isRawView={isRawView} setIsRawView={setIsRawView} />
        </div>
      )}
      {isRawView ? (
        <Textarea
          className="whitespace-pre-wrap font-mono text-sm px-[54px] border-0 shadow-none h-full outline-none ring-0 rounded-none  focus-visible:ring-0 focus-visible:ring-offset-0"
          value={rawMarkdown}
          onChange={onChangeRawMarkdown}
        />
      ) : (
        <>
          <style jsx global>{`
            .pulse-text .bn-block-group {
              animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }

            @keyframes pulse {
              0%,
              100% {
                opacity: 1;
              }
              50% {
                opacity: 0.3;
              }
            }
          `}</style>
          <BlockNoteView
            theme="light"
            formattingToolbar={false}
            slashMenu={false}
            onCompositionStartCapture={() => (isComposition.current = true)}
            onCompositionEndCapture={() => (isComposition.current = false)}
            onChange={onChange}
            editable={
              !isStreaming || props.isEditing || !manuallyUpdatingArtifact
            }
            editor={editor}
            className={cn(
              isStreaming && !firstTokenReceived ? "pulse-text" : "",
              "custom-blocknote-theme"
            )}
          >
            <SuggestionMenuController
              getItems={async () =>
                getDefaultReactSlashMenuItems(editor).filter(
                  (z) => z.group !== "Media"
                )
              }
              triggerCharacter={"/"}
            />
          </BlockNoteView>
        </>
      )}
    </div>
  );
}

export const TextRenderer = React.memo(TextRendererComponent);
