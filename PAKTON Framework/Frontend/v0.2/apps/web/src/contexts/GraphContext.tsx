import { v4 as uuidv4 } from "uuid";
import { useUserContext } from "@/contexts/UserContext";
import {
  isArtifactCodeContent,
  isArtifactMarkdownContent,
  isDeprecatedArtifactType,
} from "@opencanvas/shared/utils/artifacts";
import { reverseCleanContent } from "@/lib/normalize_string";
import {
  ArtifactType,
  ArtifactV3,
  CustomModelConfig,
  GraphInput,
  ProgrammingLanguageOptions,
  RewriteArtifactMetaToolResponse,
  SearchResult,
  TextHighlight,
} from "@opencanvas/shared/types";
import { AIMessage, BaseMessage } from "@langchain/core/messages";
import { useRuns } from "@/hooks/useRuns";
import { WEB_SEARCH_RESULTS_QUERY_PARAM } from "@/constants";
import {
  DEFAULT_INPUTS,
  OC_WEB_SEARCH_RESULTS_MESSAGE_KEY,
} from "@opencanvas/shared/constants";
import {
  ALL_MODEL_NAMES,
  NON_STREAMING_TEXT_MODELS,
  NON_STREAMING_TOOL_CALLING_MODELS,
  DEFAULT_MODEL_CONFIG,
  DEFAULT_MODEL_NAME,
} from "@opencanvas/shared/models";
import { Thread } from "@langchain/langgraph-sdk";
import { useToast } from "@/hooks/use-toast";
import {
  createContext,
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  convertToArtifactV3,
  extractChunkFields,
  handleGenerateArtifactToolCallChunk,
  removeCodeBlockFormatting,
  replaceOrInsertMessageChunk,
  updateHighlightedCode,
  updateHighlightedMarkdown,
  updateRewrittenArtifact,
} from "./utils";
import {
  handleRewriteArtifactThinkingModel,
  isThinkingModel,
} from "@opencanvas/shared/utils/thinking";
import { debounce } from "lodash";
import { useThreadContext } from "./ThreadProvider";
import { useAssistantContext } from "./AssistantContext";
import { StreamWorkerService } from "@/workers/graph-stream/streamWorker";
import { useQueryState } from "nuqs";
import { createSupabaseClient } from "@/lib/supabase/client";
import { useConversationContext } from "./ConversationContext";

interface GraphData {
  runId: string | undefined;
  isStreaming: boolean;
  error: boolean;
  selectedBlocks: TextHighlight | undefined;
  messages: BaseMessage[];
  artifact: ArtifactV3 | undefined;
  updateRenderedArtifactRequired: boolean;
  isArtifactSaved: boolean;
  firstTokenReceived: boolean;
  feedbackSubmitted: boolean;
  artifactUpdateFailed: boolean;
  chatStarted: boolean;
  searchEnabled: boolean;
  setSearchEnabled: Dispatch<SetStateAction<boolean>>;
  setChatStarted: Dispatch<SetStateAction<boolean>>;
  setIsStreaming: Dispatch<SetStateAction<boolean>>;
  setFeedbackSubmitted: Dispatch<SetStateAction<boolean>>;
  setArtifact: Dispatch<SetStateAction<ArtifactV3 | undefined>>;
  setSelectedBlocks: Dispatch<SetStateAction<TextHighlight | undefined>>;
  setSelectedArtifact: (index: number) => void;
  setMessages: Dispatch<SetStateAction<BaseMessage[]>>;
  streamMessage: (params: GraphInput) => Promise<void>;
  setArtifactContent: (index: number, content: string) => void;
  clearState: () => void;
  switchSelectedThread: (thread: Thread) => void;
  setUpdateRenderedArtifactRequired: Dispatch<SetStateAction<boolean>>;
}

type GraphContentType = {
  graphData: GraphData;
};

const GraphContext = createContext<GraphContentType | undefined>(undefined);

// Shim for recent LangGraph bugfix
function extractStreamDataChunk(chunk: any) {
  if (Array.isArray(chunk)) {
    return chunk[1];
  }
  return chunk;
}

function extractStreamDataOutput(output: any) {
  if (Array.isArray(output)) {
    return output[1];
  }
  return output;
}

export function GraphProvider({ children }: { children: ReactNode }) {
  const userData = useUserContext();
  const assistantsData = useAssistantContext();
  const threadData = useThreadContext();
  const conversationData = useConversationContext();
  const { toast } = useToast();
  const { shareRun } = useRuns();
  const [chatStarted, setChatStarted] = useState(false);
  const [messages, setMessages] = useState<BaseMessage[]>([]);
  
  // Keep ref updated with latest messages
  useEffect(() => {
    currentMessagesRef.current = messages;
  }, [messages]);
  const [artifact, setArtifact] = useState<ArtifactV3>();
  const [selectedBlocks, setSelectedBlocks] = useState<TextHighlight>();
  const [isStreaming, setIsStreaming] = useState(false);
  const [updateRenderedArtifactRequired, setUpdateRenderedArtifactRequired] =
    useState(false);
  const lastSavedArtifact = useRef<ArtifactV3 | undefined>(undefined);
  const debouncedAPIUpdate = useRef(
    debounce(
      (artifact: ArtifactV3, threadId: string) =>
        updateArtifact(artifact, threadId),
      5000
    )
  ).current;
  const [isArtifactSaved, setIsArtifactSaved] = useState(true);
  const [threadSwitched, setThreadSwitched] = useState(false);
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const [runId, setRunId] = useState<string>();
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [error, setError] = useState(false);
  const [artifactUpdateFailed, setArtifactUpdateFailed] = useState(false);
  const [intermediateStreamingComplete, setIntermediateStreamingComplete] = useState(false);
  const [reportStreamingComplete, setReportStreamingComplete] = useState(false);
  const [reportStreamingInProgress, setReportStreamingInProgress] = useState(false);
  const reportStreamingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reportStreamingCompleteRef = useRef<boolean>(false); // Ref for checking in closures
  const [searchEnabled, setSearchEnabled] = useState(false);
  const pendingCharsRef = useRef<string>("");
  const streamingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessagesRef = useRef<BaseMessage[]>([]);

  const [_, setWebSearchResultsId] = useQueryState(
    WEB_SEARCH_RESULTS_QUERY_PARAM
  );

  useEffect(() => {
    if (typeof window === "undefined" || !userData.user) return;

    // Get or create a new assistant if there isn't one set in state, and we're not
    // loading all assistants already.
    if (
      !assistantsData.selectedAssistant &&
      !assistantsData.isLoadingAllAssistants
    ) {
      assistantsData.getOrCreateAssistant(userData.user.id);
    }
  }, [userData.user]);

  // Very hacky way of ensuring updateState is not called when a thread is switched
  useEffect(() => {
    if (threadSwitched) {
      const timer = setTimeout(() => {
        setThreadSwitched(false);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [threadSwitched]);

  useEffect(() => {
    return () => {
      debouncedAPIUpdate.cancel();
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current);
      }
    };
  }, [debouncedAPIUpdate]);

  useEffect(() => {
    if (!threadData.threadId) return;
    if (!messages.length || !artifact) return;
    if (updateRenderedArtifactRequired || threadSwitched || isStreaming || reportStreamingInProgress) return;
    const currentIndex = artifact.currentIndex;
    const currentContent = artifact.contents.find(
      (c) => c.index === currentIndex
    );
    if (!currentContent) return;
    if (
      (artifact.contents.length === 1 &&
        artifact.contents[0].type === "text" &&
        !artifact.contents[0].fullMarkdown) ||
      (artifact.contents[0].type === "code" && !artifact.contents[0].code)
    ) {
      // If the artifact has only one content and it's empty, we shouldn't update the state
      return;
    }

    if (
      !lastSavedArtifact.current ||
      lastSavedArtifact.current.contents !== artifact.contents
    ) {
      setIsArtifactSaved(false);
      // This means the artifact in state does not match the last saved artifact
      // We need to update
      debouncedAPIUpdate(artifact, threadData.threadId);
    }
  }, [artifact, threadData.threadId]);

  const searchOrCreateEffectRan = useRef(false);

  // Attempt to load the thread if an ID is present in query params.
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !userData.user ||
      threadData.createThreadLoading ||
      !threadData.threadId
    ) {
      return;
    }

    // Only run effect once in development
    if (searchOrCreateEffectRan.current) {
      return;
    }
    searchOrCreateEffectRan.current = true;

    // Disabled: No longer fetching threads from LangGraph API
    // Threads are managed locally via Archivist - thread will be created when user sends first message
    // threadData.getThread(threadData.threadId).then((thread) => {
    //   if (thread) {
    //     switchSelectedThread(thread);
    //     return;
    //   }
    //   threadData.setThreadId(null);
    // });
  }, [threadData.threadId, userData.user]);

  const updateArtifact = async (
    artifactToUpdate: ArtifactV3,
    threadId: string
  ) => {
    setArtifactUpdateFailed(false);
    if (isStreaming) return;

    try {
      // LangGraph server removed - artifacts are now local only
      // const client = createClient();
      // await client.threads.updateState(threadId, {
      //   values: {
      //     artifact: artifactToUpdate,
      //   },
      // });
      setIsArtifactSaved(true);
      lastSavedArtifact.current = artifactToUpdate;
    } catch (_) {
      setArtifactUpdateFailed(true);
    }
  };

  const clearState = () => {
    setMessages([]);
    setArtifact(undefined);
    setFirstTokenReceived(true);
  };

  const streamMessageV2 = async (params: GraphInput) => {
    setFirstTokenReceived(false);
    setError(false);
    pendingCharsRef.current = "";
    setIntermediateStreamingComplete(false);
    setReportStreamingComplete(false);
    reportStreamingCompleteRef.current = false; // Reset ref too
    setReportStreamingInProgress(false);
    
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current);
      streamingTimerRef.current = null;
    }
    
    if (reportStreamingTimerRef.current) {
      clearInterval(reportStreamingTimerRef.current);
      reportStreamingTimerRef.current = null;
    }
    
    if (!assistantsData.selectedAssistant) {
      toast({
        title: "Error",
        description: "No assistant ID found",
        variant: "destructive",
        duration: 5000,
      });
      return;
    }

    let currentThreadId = threadData.threadId;
    if (!currentThreadId) {
      const newThread = await threadData.createThread();
      if (!newThread) {
        toast({
          title: "Error",
          description: "Failed to create thread",
          variant: "destructive",
          duration: 5000,
        });
        return;
      }
      currentThreadId = newThread.thread_id;
    }


    const messagesInput = {
      // `messages` contains the full, unfiltered list of messages
      messages: params.messages,
      // `_messages` contains the list of messages which are included
      // in the LLMs context, including summarization messages.
      _messages: params.messages,
    };

    // TODO: update to properly pass the highlight data back
    // one field for highlighted text, and one for code
    const input = {
      ...DEFAULT_INPUTS,
      artifact,
      ...params,
      ...messagesInput,
      ...(selectedBlocks && {
        highlightedText: selectedBlocks,
      }),
      webSearchEnabled: searchEnabled,
    };
    // Add check for multiple defined fields
    const fieldsToCheck = [
      input.highlightedCode,
      input.highlightedText,
      input.language,
      input.artifactLength,
      input.regenerateWithEmojis,
      input.readingLevel,
      input.addComments,
      input.addLogs,
      input.fixBugs,
      input.portLanguage,
      input.customQuickActionId,
    ];

    if (fieldsToCheck.filter((field) => field !== undefined).length >= 2) {
      toast({
        title: "Error",
        description:
          "Can not use multiple fields (quick actions, highlights, etc.) at once. Please try again.",
        variant: "destructive",
        duration: 5000,
      });
      return;
    }

    setIsStreaming(true);
    setRunId(undefined);
    setFeedbackSubmitted(false);
    // The root level run ID of this stream
    let runId = "";
    let followupMessageId = "";
    // The ID of the message containing the thinking content.
    let thinkingMessageId = "";

    try {
      // Get authentication token
      const supabase = createSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      const workerService = new StreamWorkerService();
      const stream = workerService.streamData({
        threadId: currentThreadId,
        assistantId: assistantsData.selectedAssistant.assistant_id,
        input,
        modelName: threadData.modelName,
        modelConfigs: threadData.modelConfigs,
        accessToken: session?.access_token,
      });

      // Variables to keep track of content specific to this stream
      const prevCurrentContent = artifact
        ? artifact.contents.find((a) => a.index === artifact.currentIndex)
        : undefined;

      // The new index of the artifact that is generating
      let newArtifactIndex = 1;
      if (artifact) {
        newArtifactIndex = artifact.contents.length + 1;
      }

      // The metadata generated when re-writing an artifact
      let rewriteArtifactMeta: RewriteArtifactMetaToolResponse | undefined =
        undefined;

      // For generating an artifact
      let generateArtifactToolCallStr = "";

      // For updating code artifacts
      // All the text up until the startCharIndex
      let updatedArtifactStartContent: string | undefined = undefined;
      // All the text after the endCharIndex
      let updatedArtifactRestContent: string | undefined = undefined;
      // Whether or not the first update has been made when updating highlighted code.
      let isFirstUpdate = true;

      // The full text content of an artifact that is being rewritten.
      // This may include thinking tokens if the model generates them.
      let fullNewArtifactContent = "";
      // The response text ONLY of the artifact that is being rewritten.
      let newArtifactContent = "";

      // The updated full markdown text when using the highlight update tool
      let highlightedText: TextHighlight | undefined = undefined;

      // The ID of the message for the web search operation during this turn
      let webSearchMessageId = "";

      for await (const chunk of stream) {
        if (chunk.event === "error") {
          const errorMessage =
            chunk?.data?.message || "Unknown error. Please try again.";
          toast({
            title: "Error generating content",
            description: errorMessage,
            variant: "destructive",
            duration: 5000,
          });
          setError(true);
          setIsStreaming(false);
          break;
        }

        // Handle Archivist SSE stream with steps
        if (chunk.event === "archivist_stream_steps") {
          const { type, thread_id, step, error: errorMsg } = chunk.data;
          
          if (type === "step" && step) {
            // Handle intermediate steps from Archivist
            const { content, message_type, tool_calls, artifact } = step;
            
            // Log the complete step data
            console.log('📨 STEP RECEIVED:', {
              type: message_type,
              content: content,
              tool_calls: tool_calls,
              artifact: artifact,
              thread_id: thread_id,
              timestamp: new Date().toISOString()
            });
            
            // Skip "human" type steps - don't display these
            if (message_type?.toLowerCase() === 'human') {
              console.log('⏭️ Skipping Human step');
              continue;
            }
            
            // Update thread ID from Archivist response
            if (thread_id) {
              if (!threadData.threadId) {
                threadData.setThreadId(thread_id);
              }
              currentThreadId = thread_id;
            }
            
            // Handle "ai" type steps (final response content)
            if (message_type?.toLowerCase() === 'ai') {
              console.log('🤖 AI step:', content?.substring(0, 50) + '...');
              
              // Create message on first AI step if needed
              if (!followupMessageId) {
                followupMessageId = `ai-${Date.now()}`;
                setMessages((prev) => [
                  ...prev,
                  new AIMessage({
                    id: followupMessageId,
                    content: "",
                    additional_kwargs: {
                      aiSteps: [],
                      interrogationCalls: [],
                      intermediateContent: "",
                    },
                  }),
                ]);
                setFirstTokenReceived(true);
              }
              
              // Check if this AI step has interrogation tool calls
              const interrogationCall = tool_calls?.find((tc: any) => tc.name === 'interrogation');
              
              // If this is an AI step with interrogation, stream the content as intermediate
              if (interrogationCall) {
                // Start character-by-character streaming of intermediate content
                let charIndex = 0;
                pendingCharsRef.current = content || '';
                
                // Update message with interrogation call
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id === followupMessageId) {
                      const currentAiSteps: any[] = Array.isArray(msg.additional_kwargs?.aiSteps) ? msg.additional_kwargs.aiSteps : [];
                      const currentInterrogationCalls: any[] = Array.isArray(msg.additional_kwargs?.interrogationCalls) ? msg.additional_kwargs.interrogationCalls : [];
                      
                      return new AIMessage({
                        id: followupMessageId,
                        content: msg.content,
                        additional_kwargs: {
                          ...msg.additional_kwargs,
                          aiSteps: [
                            ...currentAiSteps,
                            {
                              content: content || '',
                              timestamp: Date.now(),
                              toolCalls: tool_calls || [],
                              hasInterrogation: true,
                            }
                          ],
                          interrogationCalls: [
                            ...currentInterrogationCalls,
                            {
                              arguments: interrogationCall.arguments,
                              timestamp: Date.now(),
                              isActive: true,
                              showIndicator: false, // Don't show until streaming completes
                            }
                          ],
                          intermediateContent: msg.additional_kwargs?.intermediateContent || '',
                        },
                      });
                    }
                    return msg;
                  })
                );
                
                // Stream intermediate content character by character
                streamingTimerRef.current = setInterval(() => {
                  if (charIndex < pendingCharsRef.current.length) {
                    const char = pendingCharsRef.current[charIndex];
                    charIndex++;
                    
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === followupMessageId
                          ? new AIMessage({
                              id: followupMessageId,
                              content: msg.content,
                              additional_kwargs: {
                                ...msg.additional_kwargs,
                                intermediateContent: msg.additional_kwargs?.intermediateContent + char,
                              },
                            })
                          : msg
                      )
                    );
                  } else {
                    // All pending characters rendered
                    if (streamingTimerRef.current) {
                      clearInterval(streamingTimerRef.current);
                      streamingTimerRef.current = null;
                    }
                    pendingCharsRef.current = "";
                    setIntermediateStreamingComplete(true);
                    
                    // Now show the interrogation indicator
                    setMessages((prev) =>
                      prev.map((msg) => {
                        if (msg.id === followupMessageId) {
                          const currentInterrogationCalls: any[] = Array.isArray(msg.additional_kwargs?.interrogationCalls) ? msg.additional_kwargs.interrogationCalls : [];
                          return new AIMessage({
                            id: followupMessageId,
                            content: msg.content,
                            additional_kwargs: {
                              ...msg.additional_kwargs,
                              interrogationCalls: currentInterrogationCalls.map((call: any) => ({
                                ...call,
                                showIndicator: true,
                              })),
                            },
                          });
                        }
                        return msg;
                      })
                    );
                  }
                }, 5);
              } else {
                // Regular AI step without interrogation - store for final response
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id === followupMessageId) {
                      const currentAiSteps: any[] = Array.isArray(msg.additional_kwargs?.aiSteps) ? msg.additional_kwargs.aiSteps : [];
                      
                      return new AIMessage({
                        id: followupMessageId,
                        content: msg.content,
                        additional_kwargs: {
                          ...msg.additional_kwargs,
                          aiSteps: [
                            ...currentAiSteps,
                            {
                              content: content || '',
                              timestamp: Date.now(),
                              toolCalls: tool_calls || [],
                              hasInterrogation: false,
                            }
                          ],
                        },
                      });
                    }
                    return msg;
                  })
                );
              }
            } else if (message_type?.toLowerCase() === 'tool') {
              // Handle "tool" type steps - check for report artifact
              console.log('🔧 Tool step - tool result');
              
              // Create message if needed
              if (!followupMessageId) {
                followupMessageId = `ai-${Date.now()}`;
                setMessages((prev) => [
                  ...prev,
                  new AIMessage({
                    id: followupMessageId,
                    content: "",
                    additional_kwargs: {
                      aiSteps: [],
                      interrogationCalls: [],
                    },
                  }),
                ]);
                setFirstTokenReceived(true);
              }
              
              // Check if artifact contains a report
              if (artifact && typeof artifact === 'object') {
                const reportContent = artifact.report || artifact.content;
                if (reportContent) {
                  console.log('📄 Report artifact found, streaming to canvas');
                  console.log(`📄 Report length: ${reportContent.length} characters`);
                  
                  // Mark report streaming as in progress
                  setReportStreamingInProgress(true);
                  
                  // Initialize artifact with empty content
                  setFirstTokenReceived(true);
                  setArtifact({
                    currentIndex: 1,
                    contents: [
                      {
                        index: 1,
                        type: "text",
                        title: artifact.title || "Interrogation Report",
                        fullMarkdown: "",
                      }
                    ]
                  });
                  
                  // Stream the report content in chunks for better performance and reliability
                  // Using optimized chunk size and interval to prevent batching interruptions
                  const CHUNK_SIZE = 50; // Characters per chunk - smaller chunks for character-like streaming
                  const CHUNK_INTERVAL = 30; // ms between chunks - slower for more visible character streaming
                  let reportCharIndex = 0;
                  const reportTitle = artifact.title || "Interrogation Report";
                  
                  reportStreamingTimerRef.current = setInterval(() => {
                    if (reportCharIndex < reportContent.length) {
                      // Stream in chunks rather than single characters
                      const nextIndex = Math.min(reportCharIndex + CHUNK_SIZE, reportContent.length);
                      const streamedContent = reportContent.slice(0, nextIndex);
                      reportCharIndex = nextIndex;
                      
                      setArtifact({
                        currentIndex: 1,
                        contents: [
                          {
                            index: 1,
                            type: "text",
                            title: reportTitle,
                            fullMarkdown: streamedContent,
                          }
                        ]
                      });
                    } else {
                      console.log('📄 Report streaming completed');
                      if (reportStreamingTimerRef.current) {
                        clearInterval(reportStreamingTimerRef.current);
                        reportStreamingTimerRef.current = null;
                      }
                      setUpdateRenderedArtifactRequired(true);
                      setReportStreamingComplete(true);
                      reportStreamingCompleteRef.current = true; // Update ref for closure access
                      setReportStreamingInProgress(false);
                      
                      // Mark interrogation as complete AFTER report streaming finishes
                      setMessages((prev) =>
                        prev.map((msg) => {
                          if (msg.id === followupMessageId) {
                            const currentInterrogationCalls: any[] = Array.isArray(msg.additional_kwargs?.interrogationCalls) ? msg.additional_kwargs.interrogationCalls : [];
                            return new AIMessage({
                              id: followupMessageId,
                              content: msg.content,
                              additional_kwargs: {
                                ...msg.additional_kwargs,
                                interrogationCalls: currentInterrogationCalls.map((call: any) => ({
                                  ...call,
                                  isActive: false,
                                })),
                              },
                            });
                          }
                          return msg;
                        })
                      );
                    }
                  }, CHUNK_INTERVAL); // Interval between chunks
                } else {
                  // No report content, mark interrogation as complete immediately
                  setMessages((prev) =>
                    prev.map((msg) => {
                      if (msg.id === followupMessageId) {
                        const currentInterrogationCalls: any[] = Array.isArray(msg.additional_kwargs?.interrogationCalls) ? msg.additional_kwargs.interrogationCalls : [];
                        return new AIMessage({
                          id: followupMessageId,
                          content: msg.content,
                          additional_kwargs: {
                            ...msg.additional_kwargs,
                            interrogationCalls: currentInterrogationCalls.map((call: any) => ({
                              ...call,
                              isActive: false,
                            })),
                          },
                        });
                      }
                      return msg;
                    })
                  );
                }
              } else {
                // No artifact, mark interrogation as complete immediately
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id === followupMessageId) {
                      const currentInterrogationCalls: any[] = Array.isArray(msg.additional_kwargs?.interrogationCalls) ? msg.additional_kwargs.interrogationCalls : [];
                      return new AIMessage({
                        id: followupMessageId,
                        content: msg.content,
                        additional_kwargs: {
                          ...msg.additional_kwargs,
                          interrogationCalls: currentInterrogationCalls.map((call: any) => ({
                            ...call,
                            isActive: false,
                          })),
                        },
                      });
                    }
                    return msg;
                  })
                );
              }
            }
          } else if (type === "complete") {
            console.log('✅ Stream completed');
            
            // Refresh conversations when stream completes
            conversationData.refreshConversations().catch(console.error);
            
            // Wait for report streaming to complete before starting final AI message streaming
            const startFinalStreaming = () => {
              // Find the last AI message to use as the final response content
              const currentMessages = currentMessagesRef.current;
              const aiMessage = currentMessages.find(msg => msg.id === followupMessageId) as AIMessage | undefined;
              
              if (aiMessage && aiMessage.additional_kwargs?.aiSteps) {
                const aiSteps: any[] = Array.isArray(aiMessage.additional_kwargs.aiSteps) ? aiMessage.additional_kwargs.aiSteps : [];
                
                // Use the last AI step as the final content if available
                if (aiSteps.length > 0) {
                  const lastAiStep = aiSteps[aiSteps.length - 1];
                  const finalContent = lastAiStep.content;
                  
                  // Update the message with empty content initially for streaming
                  setMessages((prev) =>
                    prev.map((msg) => {
                      if (msg.id === followupMessageId) {
                        return new AIMessage({
                          id: followupMessageId,
                          content: "",
                          additional_kwargs: {
                            ...msg.additional_kwargs,
                            streaming: true,
                            readyForTypewriter: true,
                          },
                        });
                      }
                      return msg;
                    })
                  );
                  
                  // Start character-by-character streaming of final content
                  let charIndex = 0;
                  pendingCharsRef.current = finalContent;
                  
                  streamingTimerRef.current = setInterval(() => {
                    if (charIndex < pendingCharsRef.current.length) {
                      const char = pendingCharsRef.current[charIndex];
                      charIndex++;
                      
                      setMessages((prev) =>
                        prev.map((msg) =>
                          msg.id === followupMessageId
                            ? new AIMessage({
                                id: followupMessageId,
                                content: msg.content + char,
                                additional_kwargs: {
                                  ...msg.additional_kwargs,
                                  streaming: charIndex < pendingCharsRef.current.length,
                                },
                              })
                            : msg
                        )
                      );
                    } else {
                      // All pending characters rendered
                      if (streamingTimerRef.current) {
                        clearInterval(streamingTimerRef.current);
                        streamingTimerRef.current = null;
                      }
                      pendingCharsRef.current = "";
                      
                      // Mark streaming as complete
                      setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === followupMessageId
                          ? new AIMessage({
                              id: followupMessageId,
                              content: msg.content,
                              additional_kwargs: {
                                ...msg.additional_kwargs,
                                streaming: false,
                                readyForTypewriter: true,
                              },
                            })
                          : msg
                      )
                    );
                    
                    // Update cache with latest messages after streaming completes
                    const threadIdToUpdate = thread_id || currentThreadId;
                    if (threadIdToUpdate) {
                      const latestMessages = currentMessagesRef.current;
                      
                      // Convert current messages to ConversationMessage format
                      const conversationMessages = latestMessages.map((msg: any) => {
                        const msgType = msg.type || (msg.constructor?.name === 'HumanMessage' ? 'human' : 'ai');
                        
                        if (msgType === 'human' || msgType === 'user') {
                          return {
                            role: 'user' as const,
                            content: msg.content || '',
                          };
                        } else {
                          return {
                            role: 'assistant' as const,
                            content: msg.content || '',
                            aiSteps: msg.additional_kwargs?.aiSteps || [],
                            interrogationCalls: msg.additional_kwargs?.interrogationCalls || [],
                          };
                        }
                      });
                      
                      // Update the cache with the latest messages
                      console.log(`[GraphContext] Updating cache for thread ${threadIdToUpdate} with ${conversationMessages.length} messages`);
                      conversationData.updateConversationMessages(threadIdToUpdate, conversationMessages);
                    }
                    
                    setIsStreaming(false);
                      }
                    }, 5);
                  }
                } else {
                  // No AI steps found, just finish streaming
                  setIsStreaming(false);
                }
              };
            
            // Check if we need to wait for report streaming to complete
            if (reportStreamingTimerRef.current !== null) {
              console.log('⏳ Waiting for report streaming to complete before starting final AI message');
              // Report is still streaming, wait for it to complete
              let pollAttempts = 0;
              const maxPollAttempts = 1200; // 120 seconds max (1200 * 100ms) - generous timeout for large reports
              const checkReportComplete = setInterval(() => {
                pollAttempts++;
                // Use ref instead of state to avoid closure issues
                if (reportStreamingCompleteRef.current) {
                  console.log('✅ Report streaming completed, starting final AI message');
                  clearInterval(checkReportComplete);
                  startFinalStreaming();
                } else if (reportStreamingTimerRef.current === null) {
                  // Timer was cleared, streaming must be complete
                  console.log('✅ Report streaming timer cleared, starting final AI message');
                  clearInterval(checkReportComplete);
                  startFinalStreaming();
                } else if (pollAttempts >= maxPollAttempts) {
                  console.warn('⚠️ Report streaming timeout, starting final AI message anyway');
                  // Clean up the streaming timer if it's still running
                  if (reportStreamingTimerRef.current) {
                    clearInterval(reportStreamingTimerRef.current);
                    reportStreamingTimerRef.current = null;
                  }
                  clearInterval(checkReportComplete);
                  startFinalStreaming();
                }
              }, 100);
            } else {
              console.log('▶️ No report streaming, starting final AI message immediately');
              // No report streaming, start final streaming immediately
              startFinalStreaming();
            }
            
            break;
          } else if (type === "error") {
            console.error('❌ Stream error:', errorMsg);
            const errorMessage = errorMsg || 'An error occurred during streaming';
            
            toast({
              title: "Error generating content",
              description: errorMessage,
              variant: "destructive",
              duration: 5000,
            });
            
            setError(true);
            setIsStreaming(false);
            break;
          }
          continue;
        }

        try {
          const {
            runId: runId_,
            event,
            langgraphNode,
            nodeInput,
            nodeChunk,
            nodeOutput,
            taskName,
          } = extractChunkFields(chunk);

          if (!runId && runId_) {
            runId = runId_;
            setRunId(runId);
          }

          if (event === "on_chain_start") {
            if (langgraphNode === "updateHighlightedText") {
              highlightedText = nodeInput?.highlightedText;
            }

            if (langgraphNode === "queryGenerator" && !webSearchMessageId) {
              webSearchMessageId = `web-search-results-${uuidv4()}`;
              // The web search is starting. Add a new message.
              setMessages((prev) => {
                return [
                  ...prev,
                  new AIMessage({
                    id: webSearchMessageId,
                    content: "",
                    additional_kwargs: {
                      [OC_WEB_SEARCH_RESULTS_MESSAGE_KEY]: true,
                      webSearchResults: [],
                      webSearchStatus: "searching",
                    },
                  }),
                ];
              });
              // Set the query param to trigger the UI
              setWebSearchResultsId(webSearchMessageId);
            }
          }

          if (event === "on_chat_model_stream") {
            // These are generating new messages to insert to the chat window.
            if (
              ["generateFollowup", "replyToGeneralInput"].includes(
                langgraphNode
              )
            ) {
              const message = extractStreamDataChunk(nodeChunk);
              if (!followupMessageId) {
                followupMessageId = message.id;
              }
              setMessages((prevMessages) =>
                replaceOrInsertMessageChunk(prevMessages, message)
              );
            }

            if (langgraphNode === "generateArtifact") {
              const message = extractStreamDataChunk(nodeChunk);

              // Accumulate content
              if (
                message?.tool_call_chunks?.length > 0 &&
                typeof message?.tool_call_chunks?.[0]?.args === "string"
              ) {
                generateArtifactToolCallStr += message.tool_call_chunks[0].args;
              } else if (
                message?.content &&
                typeof message?.content === "string"
              ) {
                generateArtifactToolCallStr += message.content;
              }

              // Process accumulated content with rate limiting
              const result = handleGenerateArtifactToolCallChunk(
                generateArtifactToolCallStr
              );

              if (result) {
                if (result === "continue") {
                  continue;
                } else if (typeof result === "object") {
                  if (!firstTokenReceived) {
                    setFirstTokenReceived(true);
                  }
                  // Use debounced setter to prevent too frequent updates
                  setArtifact(result);
                }
              }
            }

            if (langgraphNode === "updateHighlightedText") {
              const message = extractStreamDataChunk(nodeChunk);
              if (!message) {
                continue;
              }
              if (!artifact) {
                console.error(
                  "No artifacts found when updating highlighted markdown..."
                );
                continue;
              }
              if (!highlightedText) {
                toast({
                  title: "Error",
                  description: "No highlighted text found",
                  variant: "destructive",
                  duration: 5000,
                });
                continue;
              }
              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!isArtifactMarkdownContent(prevCurrentContent)) {
                toast({
                  title: "Error",
                  description: "Received non markdown block update",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              const partialUpdatedContent = message.content || "";
              const startIndexOfHighlightedText =
                highlightedText.fullMarkdown.indexOf(
                  highlightedText.markdownBlock
                );

              if (
                updatedArtifactStartContent === undefined &&
                updatedArtifactRestContent === undefined
              ) {
                // Initialize the start and rest content on first chunk
                updatedArtifactStartContent =
                  highlightedText.fullMarkdown.slice(
                    0,
                    startIndexOfHighlightedText
                  );
                updatedArtifactRestContent = highlightedText.fullMarkdown.slice(
                  startIndexOfHighlightedText +
                    highlightedText.markdownBlock.length
                );
              }

              if (
                updatedArtifactStartContent !== undefined &&
                updatedArtifactRestContent !== undefined
              ) {
                updatedArtifactStartContent += partialUpdatedContent;
              }

              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }
                return updateHighlightedMarkdown(
                  prev,
                  `${updatedArtifactStartContent}${updatedArtifactRestContent}`,
                  newArtifactIndex,
                  prevCurrentContent,
                  firstUpdateCopy
                );
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (langgraphNode === "updateArtifact") {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!params.highlightedCode) {
                toast({
                  title: "Error",
                  description: "No highlighted code found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              const partialUpdatedContent =
                extractStreamDataChunk(nodeChunk)?.content || "";
              const { startCharIndex, endCharIndex } = params.highlightedCode;

              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (prevCurrentContent.type !== "code") {
                toast({
                  title: "Error",
                  description: "Received non code block update",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              if (
                updatedArtifactStartContent === undefined &&
                updatedArtifactRestContent === undefined
              ) {
                updatedArtifactStartContent = prevCurrentContent.code.slice(
                  0,
                  startCharIndex
                );
                updatedArtifactRestContent =
                  prevCurrentContent.code.slice(endCharIndex);
              } else {
                // One of the above have been populated, now we can update the start to contain the new text.
                updatedArtifactStartContent += partialUpdatedContent;
              }
              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }
                const content = removeCodeBlockFormatting(
                  `${updatedArtifactStartContent}${updatedArtifactRestContent}`
                );
                return updateHighlightedCode(
                  prev,
                  content,
                  newArtifactIndex,
                  prevCurrentContent,
                  firstUpdateCopy
                );
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (
              langgraphNode === "rewriteArtifact" &&
              taskName === "rewrite_artifact_model_call" &&
              rewriteArtifactMeta
            ) {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              fullNewArtifactContent +=
                extractStreamDataChunk(nodeChunk)?.content || "";

              if (isThinkingModel(threadData.modelName)) {
                if (!thinkingMessageId) {
                  thinkingMessageId = `thinking-${uuidv4()}`;
                }
                newArtifactContent = handleRewriteArtifactThinkingModel({
                  newArtifactContent: fullNewArtifactContent,
                  setMessages,
                  thinkingMessageId,
                });
              } else {
                newArtifactContent = fullNewArtifactContent;
              }

              // Ensure we have the language to update the artifact with
              let artifactLanguage = params.portLanguage || undefined;
              if (
                !artifactLanguage &&
                rewriteArtifactMeta.type === "code" &&
                rewriteArtifactMeta.language
              ) {
                // If the type is `code` we should have a programming language populated
                // in the rewriteArtifactMeta and can use that.
                artifactLanguage =
                  rewriteArtifactMeta.language as ProgrammingLanguageOptions;
              } else if (!artifactLanguage) {
                artifactLanguage =
                  (prevCurrentContent?.title as ProgrammingLanguageOptions) ??
                  "other";
              }

              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }

                let content = newArtifactContent;
                if (!rewriteArtifactMeta) {
                  console.error(
                    "No rewrite artifact meta found when updating artifact"
                  );
                  return prev;
                }
                if (rewriteArtifactMeta.type === "code") {
                  content = removeCodeBlockFormatting(content);
                }

                return updateRewrittenArtifact({
                  prevArtifact: prev,
                  newArtifactContent: content,
                  rewriteArtifactMeta: rewriteArtifactMeta,
                  prevCurrentContent,
                  newArtifactIndex,
                  isFirstUpdate: firstUpdateCopy,
                  artifactLanguage,
                });
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (
              [
                "rewriteArtifactTheme",
                "rewriteCodeArtifactTheme",
                "customAction",
              ].includes(langgraphNode)
            ) {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              fullNewArtifactContent +=
                extractStreamDataChunk(nodeChunk)?.content || "";

              if (isThinkingModel(threadData.modelName)) {
                if (!thinkingMessageId) {
                  thinkingMessageId = `thinking-${uuidv4()}`;
                }
                newArtifactContent = handleRewriteArtifactThinkingModel({
                  newArtifactContent: fullNewArtifactContent,
                  setMessages,
                  thinkingMessageId,
                });
              } else {
                newArtifactContent = fullNewArtifactContent;
              }

              // Ensure we have the language to update the artifact with
              const artifactLanguage =
                params.portLanguage ||
                (isArtifactCodeContent(prevCurrentContent)
                  ? prevCurrentContent.language
                  : "other");

              const langGraphNode = langgraphNode;
              let artifactType: ArtifactType;
              if (langGraphNode === "rewriteCodeArtifactTheme") {
                artifactType = "code";
              } else if (langGraphNode === "rewriteArtifactTheme") {
                artifactType = "text";
              } else {
                artifactType = prevCurrentContent.type;
              }
              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }

                let content = newArtifactContent;
                if (artifactType === "code") {
                  content = removeCodeBlockFormatting(content);
                }

                return updateRewrittenArtifact({
                  prevArtifact: prev ?? artifact,
                  newArtifactContent: content,
                  rewriteArtifactMeta: {
                    type: artifactType,
                    title: prevCurrentContent.title,
                    language: artifactLanguage,
                  },
                  prevCurrentContent,
                  newArtifactIndex,
                  isFirstUpdate: firstUpdateCopy,
                  artifactLanguage,
                });
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }
          }

          if (event === "on_chat_model_end") {
            if (
              langgraphNode === "rewriteArtifact" &&
              taskName === "rewrite_artifact_model_call" &&
              rewriteArtifactMeta &&
              NON_STREAMING_TEXT_MODELS.some((m) => m === threadData.modelName)
            ) {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              const message = extractStreamDataOutput(nodeOutput);

              fullNewArtifactContent += message.content || "";

              // Ensure we have the language to update the artifact with
              let artifactLanguage = params.portLanguage || undefined;
              if (
                !artifactLanguage &&
                rewriteArtifactMeta.type === "code" &&
                rewriteArtifactMeta.language
              ) {
                // If the type is `code` we should have a programming language populated
                // in the rewriteArtifactMeta and can use that.
                artifactLanguage =
                  rewriteArtifactMeta.language as ProgrammingLanguageOptions;
              } else if (!artifactLanguage) {
                artifactLanguage =
                  (prevCurrentContent?.title as ProgrammingLanguageOptions) ??
                  "other";
              }

              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }

                let content = fullNewArtifactContent;
                if (!rewriteArtifactMeta) {
                  console.error(
                    "No rewrite artifact meta found when updating artifact"
                  );
                  return prev;
                }
                if (rewriteArtifactMeta.type === "code") {
                  content = removeCodeBlockFormatting(content);
                }

                return updateRewrittenArtifact({
                  prevArtifact: prev,
                  newArtifactContent: content,
                  rewriteArtifactMeta: rewriteArtifactMeta,
                  prevCurrentContent,
                  newArtifactIndex,
                  isFirstUpdate: firstUpdateCopy,
                  artifactLanguage,
                });
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (
              langgraphNode === "updateHighlightedText" &&
              NON_STREAMING_TEXT_MODELS.some((m) => m === threadData.modelName)
            ) {
              const message = extractStreamDataOutput(nodeOutput);
              if (!message) {
                continue;
              }
              if (!artifact) {
                console.error(
                  "No artifacts found when updating highlighted markdown..."
                );
                continue;
              }
              if (!highlightedText) {
                toast({
                  title: "Error",
                  description: "No highlighted text found",
                  variant: "destructive",
                  duration: 5000,
                });
                continue;
              }
              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!isArtifactMarkdownContent(prevCurrentContent)) {
                toast({
                  title: "Error",
                  description: "Received non markdown block update",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              const partialUpdatedContent = message.content || "";
              const startIndexOfHighlightedText =
                highlightedText.fullMarkdown.indexOf(
                  highlightedText.markdownBlock
                );

              if (
                updatedArtifactStartContent === undefined &&
                updatedArtifactRestContent === undefined
              ) {
                // Initialize the start and rest content on first chunk
                updatedArtifactStartContent =
                  highlightedText.fullMarkdown.slice(
                    0,
                    startIndexOfHighlightedText
                  );
                updatedArtifactRestContent = highlightedText.fullMarkdown.slice(
                  startIndexOfHighlightedText +
                    highlightedText.markdownBlock.length
                );
              }

              if (
                updatedArtifactStartContent !== undefined &&
                updatedArtifactRestContent !== undefined
              ) {
                updatedArtifactStartContent += partialUpdatedContent;
              }

              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }
                return updateHighlightedMarkdown(
                  prev,
                  `${updatedArtifactStartContent}${updatedArtifactRestContent}`,
                  newArtifactIndex,
                  prevCurrentContent,
                  firstUpdateCopy
                );
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (
              langgraphNode === "updateArtifact" &&
              NON_STREAMING_TEXT_MODELS.some((m) => m === threadData.modelName)
            ) {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!params.highlightedCode) {
                toast({
                  title: "Error",
                  description: "No highlighted code found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              const message = extractStreamDataOutput(nodeOutput);
              if (!message) {
                continue;
              }

              const partialUpdatedContent = message.content || "";
              const { startCharIndex, endCharIndex } = params.highlightedCode;

              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (prevCurrentContent.type !== "code") {
                toast({
                  title: "Error",
                  description: "Received non code block update",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }

              if (
                updatedArtifactStartContent === undefined &&
                updatedArtifactRestContent === undefined
              ) {
                updatedArtifactStartContent =
                  prevCurrentContent.code.slice(0, startCharIndex) +
                  partialUpdatedContent;
                updatedArtifactRestContent =
                  prevCurrentContent.code.slice(endCharIndex);
              }
              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }
                const content = removeCodeBlockFormatting(
                  `${updatedArtifactStartContent}${updatedArtifactRestContent}`
                );
                return updateHighlightedCode(
                  prev,
                  content,
                  newArtifactIndex,
                  prevCurrentContent,
                  firstUpdateCopy
                );
              });

              if (isFirstUpdate) {
                isFirstUpdate = false;
              }
            }

            if (
              [
                "rewriteArtifactTheme",
                "rewriteCodeArtifactTheme",
                "customAction",
              ].includes(langgraphNode) &&
              NON_STREAMING_TEXT_MODELS.some((m) => m === threadData.modelName)
            ) {
              if (!artifact) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              if (!prevCurrentContent) {
                toast({
                  title: "Error",
                  description: "Original artifact not found",
                  variant: "destructive",
                  duration: 5000,
                });
                return;
              }
              const message = extractStreamDataOutput(nodeOutput);
              fullNewArtifactContent += message?.content || "";

              // Ensure we have the language to update the artifact with
              const artifactLanguage =
                params.portLanguage ||
                (isArtifactCodeContent(prevCurrentContent)
                  ? prevCurrentContent.language
                  : "other");

              let artifactType: ArtifactType;
              if (langgraphNode === "rewriteCodeArtifactTheme") {
                artifactType = "code";
              } else if (langgraphNode === "rewriteArtifactTheme") {
                artifactType = "text";
              } else {
                artifactType = prevCurrentContent.type;
              }
              const firstUpdateCopy = isFirstUpdate;
              setFirstTokenReceived(true);
              setArtifact((prev) => {
                if (!prev) {
                  throw new Error("No artifact found when updating markdown");
                }

                let content = fullNewArtifactContent;
                if (artifactType === "code") {
                  content = removeCodeBlockFormatting(content);
                }

                return updateRewrittenArtifact({
                  prevArtifact: prev ?? artifact,
                  newArtifactContent: content,
                  rewriteArtifactMeta: {
                    type: artifactType,
                    title: prevCurrentContent.title,
                    language: artifactLanguage,
                  },
                  prevCurrentContent,
                  newArtifactIndex,
                  isFirstUpdate: firstUpdateCopy,
                  artifactLanguage,
                });
              });
            }

            if (
              ["generateFollowup", "replyToGeneralInput"].includes(
                langgraphNode
              ) &&
              !followupMessageId &&
              NON_STREAMING_TEXT_MODELS.some((m) => m === threadData.modelName)
            ) {
              const message = extractStreamDataOutput(nodeOutput);
              followupMessageId = message.id;
              setMessages((prevMessages) =>
                replaceOrInsertMessageChunk(prevMessages, message)
              );
            }
          }

          if (event === "on_chain_end") {
            if (
              langgraphNode === "rewriteArtifact" &&
              taskName === "optionally_update_artifact_meta"
            ) {
              rewriteArtifactMeta = nodeOutput;
            }

            if (langgraphNode === "search" && webSearchMessageId) {
              const output = nodeOutput as {
                webSearchResults: SearchResult[];
              };

              setMessages((prev) => {
                return prev.map((m) => {
                  if (m.id !== webSearchMessageId) return m;

                  return new AIMessage({
                    ...m,
                    additional_kwargs: {
                      ...m.additional_kwargs,
                      webSearchResults: output.webSearchResults,
                      webSearchStatus: "done",
                    },
                  });
                });
              });
            }

            if (
              langgraphNode === "generateArtifact" &&
              !generateArtifactToolCallStr &&
              NON_STREAMING_TOOL_CALLING_MODELS.some(
                (m) => m === threadData.modelName
              )
            ) {
              const message = nodeOutput;
              generateArtifactToolCallStr +=
                message?.tool_call_chunks?.[0]?.args || message?.content || "";
              const result = handleGenerateArtifactToolCallChunk(
                generateArtifactToolCallStr
              );
              if (result && result === "continue") {
                continue;
              } else if (result && typeof result === "object") {
                setFirstTokenReceived(true);
                setArtifact(result);
              }
            }
          }
        } catch (e: any) {
          console.error(
            "Failed to parse stream chunk",
            chunk,
            "\n\nError:\n",
            e
          );

          let errorMessage = "Unknown error. Please try again.";
          if (typeof e === "object" && e?.message) {
            errorMessage = e.message;
          }

          toast({
            title: "Error generating content",
            description: errorMessage,
            variant: "destructive",
            duration: 5000,
          });
          setError(true);
          setIsStreaming(false);
          break;
        }
      }
      lastSavedArtifact.current = artifact;
    } catch (e) {
      console.error("Failed to stream message", e);
    } finally {
      setSelectedBlocks(undefined);
      setIsStreaming(false);
    }

    if (runId) {
      // Chain `.then` to not block the stream
      shareRun(runId).then(async (sharedRunURL) => {
        setMessages((prevMessages) => {
          const newMsgs = prevMessages.map((msg) => {
            if (
              msg.id === followupMessageId &&
              !(msg as AIMessage).tool_calls?.find(
                (tc) => tc.name === "langsmith_tool_ui"
              )
            ) {
              const toolCall = {
                name: "langsmith_tool_ui",
                args: { sharedRunURL },
                id: sharedRunURL
                  ?.split("https://smith.langchain.com/public/")[1]
                  .split("/")[0],
              };
              const castMsg = msg as AIMessage;
              const newMessageWithToolCall = new AIMessage({
                ...castMsg,
                content: castMsg.content,
                id: castMsg.id,
                tool_calls: castMsg.tool_calls
                  ? [...castMsg.tool_calls, toolCall]
                  : [toolCall],
              });
              return newMessageWithToolCall;
            }

            return msg;
          });
          return newMsgs;
        });
      });
    }
  };

  const setSelectedArtifact = (index: number) => {
    setUpdateRenderedArtifactRequired(true);
    setThreadSwitched(true);

    setArtifact((prev) => {
      if (!prev) {
        toast({
          title: "Error",
          description: "No artifactV2 found",
          variant: "destructive",
          duration: 5000,
        });
        return prev;
      }
      const newArtifact = {
        ...prev,
        currentIndex: index,
      };
      lastSavedArtifact.current = newArtifact;
      return newArtifact;
    });
  };

  const setArtifactContent = (index: number, content: string) => {
    setArtifact((prev) => {
      if (!prev) {
        toast({
          title: "Error",
          description: "No artifact found",
          variant: "destructive",
          duration: 5000,
        });
        return prev;
      }
      const newArtifact = {
        ...prev,
        currentIndex: index,
        contents: prev.contents.map((a) => {
          if (a.index === index && a.type === "code") {
            return {
              ...a,
              code: reverseCleanContent(content),
            };
          }
          return a;
        }),
      };
      return newArtifact;
    });
  };

  const switchSelectedThread = (thread: Thread) => {
    setUpdateRenderedArtifactRequired(true);
    setThreadSwitched(true);
    setChatStarted(true);

    // Set the thread ID in state. Then set in cookies so a new thread
    // isn't created on page load if one already exists.
    threadData.setThreadId(thread.thread_id);

    // Set the model name and config
    if (thread.metadata?.customModelName) {
      threadData.setModelName(
        thread.metadata.customModelName as ALL_MODEL_NAMES
      );
      threadData.setModelConfig(
        thread.metadata.customModelName as ALL_MODEL_NAMES,
        thread.metadata.modelConfig as CustomModelConfig
      );
    } else {
      threadData.setModelName(DEFAULT_MODEL_NAME);
      threadData.setModelConfig(DEFAULT_MODEL_NAME, DEFAULT_MODEL_CONFIG);
    }

    // Check if this is a conversation-based thread (from API) or a legacy LangGraph thread
    const isConversationThread = !thread.values || Object.keys(thread.values).length === 0;
    
    if (isConversationThread) {
      // This is an API-based conversation - clear messages and artifacts
      // since we don't have historical data, just the thread_id for future messages
      setMessages([]);
      setArtifact(undefined);
      lastSavedArtifact.current = undefined;
      
      // Show a toast to inform the user they've switched to a conversation
      if (thread.metadata?.thread_title) {
        toast({
          title: "Conversation Selected",
          description: `Switched to "${thread.metadata.thread_title}". Continue the conversation below.`,
          duration: 3000,
        });
      }
      return;
    }

    // Legacy LangGraph thread handling
    const castValues: {
      artifact: ArtifactV3 | undefined;
      messages: Record<string, any>[] | undefined;
    } = {
      artifact: undefined,
      messages: (thread.values as Record<string, any>)?.messages || undefined,
    };
    const castThreadValues = thread.values as Record<string, any>;
    if (castThreadValues?.artifact) {
      if (isDeprecatedArtifactType(castThreadValues.artifact)) {
        castValues.artifact = convertToArtifactV3(castThreadValues.artifact);
      } else {
        castValues.artifact = castThreadValues.artifact;
      }
    } else {
      castValues.artifact = undefined;
    }
    lastSavedArtifact.current = castValues?.artifact;

    if (!castValues?.messages?.length) {
      setMessages([]);
      setArtifact(castValues?.artifact);
      return;
    }
    setArtifact(castValues?.artifact);
    setMessages(
      castValues.messages.map((msg: Record<string, any>) => {
        if (msg.response_metadata?.langSmithRunURL) {
          msg.tool_calls = msg.tool_calls ?? [];
          msg.tool_calls.push({
            name: "langsmith_tool_ui",
            args: { sharedRunURL: msg.response_metadata.langSmithRunURL },
            id: msg.response_metadata.langSmithRunURL
              ?.split("https://smith.langchain.com/public/")[1]
              .split("/")[0],
          });
        }
        return msg as BaseMessage;
      })
    );
  };

  const contextValue: GraphContentType = {
    graphData: {
      runId,
      isStreaming,
      error,
      selectedBlocks,
      messages,
      artifact,
      updateRenderedArtifactRequired,
      isArtifactSaved,
      firstTokenReceived,
      feedbackSubmitted,
      chatStarted,
      artifactUpdateFailed,
      searchEnabled,
      setSearchEnabled,
      setChatStarted,
      setIsStreaming,
      setFeedbackSubmitted,
      setArtifact,
      setSelectedBlocks,
      setSelectedArtifact,
      setMessages,
      streamMessage: streamMessageV2,
      setArtifactContent,
      clearState,
      switchSelectedThread,
      setUpdateRenderedArtifactRequired,
    },
  };

  return (
    <GraphContext.Provider value={contextValue}>
      {children}
    </GraphContext.Provider>
  );
}

export function useGraphContext() {
  const context = useContext(GraphContext);
  if (context === undefined) {
    throw new Error("useGraphContext must be used within a GraphProvider");
  }
  return context;
}
