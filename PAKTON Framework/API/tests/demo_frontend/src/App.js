import React, { useState, useRef, useEffect } from 'react';
import MessageComponent from './MessageComponent';
import './index.css';

const API_BASE_URL = 'http://localhost:5001';
const QUERY_SSE_ENDPOINT = '/query/sse';
const QUERY_STREAM_STEPS_SSE_ENDPOINT = '/query/stream_steps/sse';
const INDEX_DOCUMENT_ENDPOINT = '/index/document/';
const TASK_STATUS_ENDPOINT = '/task_status/';
const TERMINAL_STATUSES = new Set(['SUCCESS', 'FAILURE', 'REVOKED', 'IGNORED']);

const MIME_TYPES = {
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.pdf': 'application/pdf',
  '.txt': 'text/plain'
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState('');
  const [threadIdInput, setThreadIdInput] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexingStatus, setIndexingStatus] = useState('');
  const [endpointMode, setEndpointMode] = useState('simple'); // 'simple' or 'stream_steps'
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };

  const updateLastMessage = (updates) => {
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages.length > 0) {
        newMessages[newMessages.length - 1] = {
          ...newMessages[newMessages.length - 1],
          ...updates
        };
      }
      return newMessages;
    });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    addMessage(userMessage);
    const query = inputValue;
    setInputValue('');
    setIsLoading(true);
    setConnectionStatus('connecting');

    // Add loading message
    const loadingMessage = {
      id: Date.now() + 1,
      type: 'loading',
      content: 'Processing...',
      timestamp: new Date().toISOString()
    };
    addMessage(loadingMessage);

    try {
      const requestBody = {
        query: query
      };
      
      // Add thread_id only if provided
      if (threadIdInput.trim()) {
        requestBody.thread_id = threadIdInput.trim();
      }

      const endpoint = endpointMode === 'stream_steps' ? QUERY_STREAM_STEPS_SSE_ENDPOINT : QUERY_SSE_ENDPOINT;
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setConnectionStatus('connected');
      
      // Remove loading message
      setMessages(prev => prev.filter(msg => msg.type !== 'loading'));

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let assistantMessage = null;
      let fullResponseText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'chunk') {
                // Create assistant message if it doesn't exist
                if (!assistantMessage) {
                  assistantMessage = {
                    id: Date.now() + 2,
                    type: 'assistant',
                    content: '',
                    timestamp: new Date().toISOString()
                  };
                  addMessage(assistantMessage);
                }
                
                // Extract content from chunk
                const chunkData = data.chunk;
                let content = '';
                
                if (typeof chunkData === 'string') {
                  content = chunkData;
                } else if (chunkData && chunkData.messages && chunkData.messages.length > 0) {
                  const lastMessage = chunkData.messages[chunkData.messages.length - 1];
                  if (typeof lastMessage.content === 'string') {
                    content = lastMessage.content;
                  } else if (typeof lastMessage === 'string') {
                    content = lastMessage;
                  }
                }
                
                fullResponseText += content;
                updateLastMessage({ content: fullResponseText });
                
                // Update thread ID if provided
                if (data.thread_id) {
                  setCurrentThreadId(data.thread_id);
                  if (!threadIdInput.trim()) {
                    setThreadIdInput(data.thread_id);
                  }
                }
              } else if (data.type === 'step') {
                // Handle streaming steps
                const step = data.step;
                
                if (step.message_type === 'ai' && step.content) {
                  // AI response content
                  if (!assistantMessage) {
                    assistantMessage = {
                      id: Date.now() + 2,
                      type: 'assistant',
                      content: '',
                      timestamp: new Date().toISOString()
                    };
                    addMessage(assistantMessage);
                  }
                  fullResponseText = step.content;
                  updateLastMessage({ content: fullResponseText });
                } else if (step.tool_calls && step.tool_calls.length > 0) {
                  // Tool call step
                  const toolCallsText = step.tool_calls.map(tc => 
                    `🔧 Tool: ${tc.name}\nArguments: ${JSON.stringify(tc.arguments, null, 2)}`
                  ).join('\n\n');
                  
                  const toolMessage = {
                    id: Date.now() + Math.random(),
                    type: 'step',
                    content: toolCallsText,
                    timestamp: new Date().toISOString()
                  };
                  addMessage(toolMessage);
                } else if (step.message_type === 'tool' && step.content) {
                  // Tool response
                  const toolResponseMessage = {
                    id: Date.now() + Math.random(),
                    type: 'step',
                    content: `📊 Tool Response:\n${step.content.substring(0, 200)}${step.content.length > 200 ? '...' : ''}`,
                    timestamp: new Date().toISOString()
                  };
                  addMessage(toolResponseMessage);
                }
                
                // Update thread ID if provided
                if (data.thread_id) {
                  setCurrentThreadId(data.thread_id);
                  if (!threadIdInput.trim()) {
                    setThreadIdInput(data.thread_id);
                  }
                }
              } else if (data.type === 'complete') {
                // Stream completed
                setConnectionStatus('disconnected');
                console.log('Stream completed successfully');
                break;
              } else if (data.type === 'error') {
                // Handle error
                const errorMessage = {
                  id: Date.now() + 3,
                  type: 'error',
                  content: `Error: ${data.error}`,
                  timestamp: new Date().toISOString()
                };
                addMessage(errorMessage);
                setConnectionStatus('error');
                break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line, parseError);
            }
          }
        }
      }

    } catch (error) {
      console.error('Error:', error);
      setConnectionStatus('error');
      
      // Remove loading message
      setMessages(prev => prev.filter(msg => msg.type !== 'loading'));
      
      const errorMessage = {
        id: Date.now() + 4,
        type: 'error',
        content: `Connection error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const pollTaskStatus = async (taskId, initialInterval = 2000, maxRetries = 30, backoffFactor = 1.2) => {
    let currentInterval = initialInterval;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}${TASK_STATUS_ENDPOINT}${taskId}`);
        
        if (!response.ok) {
          throw new Error(`Status check failed: ${response.status}`);
        }

        const data = await response.json();
        const status = data.data?.task_status;

        setIndexingStatus(`Checking status (${attempt + 1}/${maxRetries}): ${status}`);

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

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsIndexing(true);
    setIndexingStatus('Uploading document...');

    try {
      // Get file extension
      const fileName = file.name;
      const fileExtension = '.' + fileName.split('.').pop().toLowerCase();
      const mimeType = MIME_TYPES[fileExtension] || 'application/octet-stream';

      // Check if file type is supported
      if (!MIME_TYPES[fileExtension]) {
        throw new Error(`Unsupported file type: ${fileExtension}. Please upload .docx, .pdf, or .txt files.`);
      }

      // Prepare form data
      const formData = new FormData();
      formData.append('file', file, fileName);
      
      const metadata = {
        title: fileName,
        author: "Demo User"
      };
      formData.append('metadata', JSON.stringify(metadata));

      // Add system message about indexing
      const indexingMessage = {
        id: Date.now(),
        type: 'system',
        content: `📄 Indexing document: ${fileName}`,
        timestamp: new Date().toISOString()
      };
      addMessage(indexingMessage);

      // Call index endpoint
      const response = await fetch(`${API_BASE_URL}${INDEX_DOCUMENT_ENDPOINT}`, {
        method: 'POST',
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

      setIndexingStatus('Document uploaded. Processing...');

      // Poll for task completion
      const taskResult = await pollTaskStatus(taskId);
      const taskStatus = taskResult.data?.task_status;
      const taskResponse = taskResult.data?.task_response;

      if (taskStatus === 'SUCCESS' && taskResponse?.status === 'SUCCESS') {
        const successMessage = {
          id: Date.now() + 1,
          type: 'system',
          content: `✅ Document "${fileName}" successfully indexed!\nDocument ID: ${taskResponse.data?.document_id || 'N/A'}`,
          timestamp: new Date().toISOString()
        };
        addMessage(successMessage);
        setIndexingStatus('Indexing complete!');
      } else {
        throw new Error(taskResponse?.message || `Indexing failed with status: ${taskStatus}`);
      }

    } catch (error) {
      console.error('Error indexing document:', error);
      const errorMessage = {
        id: Date.now() + 2,
        type: 'error',
        content: `Failed to index document: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      addMessage(errorMessage);
      setIndexingStatus('Indexing failed');
    } finally {
      setIsIndexing(false);
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      // Clear status after a delay
      setTimeout(() => setIndexingStatus(''), 3000);
    }
  };

  const handleIndexButtonClick = () => {
    fileInputRef.current?.click();
  };

  const clearConversation = () => {
    setMessages([]);
    setCurrentThreadId('');
    setThreadIdInput('');
    setConnectionStatus('disconnected');
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>PAKTON API Chat Frontend</h1>
        <p>Test your SSE endpoints with real-time streaming</p>
        
        <div className="endpoint-mode-container">
          <label>Endpoint Mode:</label>
          <div className="endpoint-toggle">
            <button
              className={`toggle-button ${endpointMode === 'simple' ? 'active' : ''}`}
              onClick={() => setEndpointMode('simple')}
              disabled={isLoading}
            >
              Simple (/query/sse)
            </button>
            <button
              className={`toggle-button ${endpointMode === 'stream_steps' ? 'active' : ''}`}
              onClick={() => setEndpointMode('stream_steps')}
              disabled={isLoading}
            >
              Stream Steps (/query/stream_steps/sse)
            </button>
          </div>
        </div>
        
        <div className="thread-id-input-container">
          <label htmlFor="thread-id-input">Thread ID (optional):</label>
          <input
            id="thread-id-input"
            type="text"
            className="thread-id-input"
            value={threadIdInput}
            onChange={(e) => setThreadIdInput(e.target.value)}
            placeholder="Leave empty for new thread or enter existing thread ID"
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="chat-messages">
        {currentThreadId && (
          <div className="thread-info">
            🧵 Active Thread ID: {currentThreadId}
          </div>
        )}
        
        {messages.map((message) => (
          <MessageComponent 
            key={message.id} 
            message={message} 
            formatTimestamp={formatTimestamp}
          />
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="input-actions">
          <div className="left-actions">
            <div className={`connection-status ${connectionStatus}`}>
              <div className="status-dot"></div>
              {connectionStatus === 'connected' && 'Streaming...'}
              {connectionStatus === 'connecting' && 'Connecting...'}
              {connectionStatus === 'disconnected' && 'Ready'}
              {connectionStatus === 'error' && 'Connection Error'}
            </div>
            
            <button 
              className="index-button" 
              onClick={handleIndexButtonClick}
              disabled={isIndexing || isLoading}
              title="Index a document (PDF, DOCX, TXT)"
            >
              {isIndexing ? '📄 Indexing...' : '📄 Index Document'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {indexingStatus && (
              <div className="indexing-status">
                {indexingStatus}
              </div>
            )}
          </div>
          
          <button className="clear-button" onClick={clearConversation}>
            Clear Chat
          </button>
        </div>
        
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Type your message to test ${endpointMode === 'stream_steps' ? '/query/stream_steps/sse' : '/query/sse'} endpoint...`}
            disabled={isLoading}
            rows={1}
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
