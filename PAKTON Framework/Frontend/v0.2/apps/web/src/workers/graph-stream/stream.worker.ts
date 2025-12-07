import { StreamConfig } from "./streamWorker.types";

const ARCHIVIST_API_URL = process.env.NEXT_PUBLIC_ARCHIVIST_API_URL ?? "http://localhost:5001";
const QUERY_SSE_ENDPOINT = "/query/stream_steps/sse";

// Since workers can't directly access the client SDK, you'll need to recreate/import necessary parts
const ctx: Worker = self as any;

ctx.addEventListener("message", async (event: MessageEvent<StreamConfig>) => {
  try {
    const { threadId, input, accessToken } = event.data;

    // Extract the user's query from the input
    // The input.messages array contains the conversation messages
    const messages = input.messages || [];
    const lastMessage = messages[messages.length - 1];
    const query = typeof lastMessage === 'string' 
      ? lastMessage 
      : lastMessage?.content || '';

    // Prepare request body for Archivist API
    const requestBody: any = {
      query: query
    };
    
    // Add thread_id if provided
    if (threadId) {
      requestBody.thread_id = threadId;
    }

    // Call Archivist SSE endpoint with streaming steps
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    };
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${ARCHIVIST_API_URL}${QUERY_SSE_ENDPOINT}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            // Transform Archivist stream_steps SSE format to internal format
            // Archivist sends: 
            // - { type: 'step', thread_id, step: { content, message_type, tool_calls, artifact } }
            // - { type: 'complete' }
            // - { type: 'error', error }
            ctx.postMessage({
              type: "chunk",
              data: JSON.stringify({
                event: "archivist_stream_steps",
                data: data
              }),
            });
          } catch (e) {
            console.error('Failed to parse SSE line:', line, e);
          }
        }
      }
    }

    ctx.postMessage({ type: "done" });
  } catch (error: any) {
    ctx.postMessage({
      type: "error",
      error: error.message,
    });
  }
});
