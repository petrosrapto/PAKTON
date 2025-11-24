# Frontend Integration Guide - Conversation Tracking

Quick reference for integrating conversation tracking in the frontend.

## Getting Started

All endpoints require JWT authentication via the `Authorization` header.

## Key Endpoints

### 1. Start or Continue a Conversation

**Endpoint:** `POST /query/sse` or `POST /query/stream_steps/sse`

**New Conversation:**
```javascript
const response = await fetch('http://localhost:5001/query/sse', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What is artificial intelligence?",
    thread_id: null,  // null or omit for new conversation
    config: {}
  })
});

// Listen to SSE stream
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      if (data.type === 'chunk') {
        console.log('Thread ID:', data.thread_id);  // Save this!
        console.log('Response:', data.chunk);
      } else if (data.type === 'complete') {
        console.log('Conversation complete');
      }
    }
  }
}
```

**Continue Existing Conversation:**
```javascript
const response = await fetch('http://localhost:5001/query/sse', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "Can you explain more about machine learning?",
    thread_id: savedThreadId,  // Use the thread_id from previous response
    config: {}
  })
});
```

### 2. Get User's Conversation History

**Endpoint:** `GET /conversations`

```javascript
const response = await fetch(
  'http://localhost:5001/conversations?limit=20&offset=0',
  {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  }
);

const result = await response.json();
console.log(result.data.conversations);
// [
//   {
//     thread_id: "abc-123",
//     user_email: "user@example.com",
//     title: null,
//     last_message: "Artificial intelligence is...",
//     created_at: "2025-11-23T10:00:00",
//     updated_at: "2025-11-23T12:00:00"
//   },
//   ...
// ]
```

### 3. Get Specific Conversation

**Endpoint:** `GET /conversations/{thread_id}`

```javascript
const response = await fetch(
  `http://localhost:5001/conversations/${threadId}`,
  {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  }
);

const result = await response.json();
console.log(result.data);
```

### 4. Delete Conversation

**Endpoint:** `DELETE /conversations/{thread_id}`

```javascript
const response = await fetch(
  `http://localhost:5001/conversations/${threadId}`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  }
);

const result = await response.json();
// { message: "Conversation deleted successfully", statusCode: 200, data: {} }
```

## React Example Component

```typescript
import React, { useState, useEffect } from 'react';

interface Conversation {
  thread_id: string;
  user_email: string;
  title: string | null;
  last_message: string | null;
  created_at: string;
  updated_at: string;
}

function ConversationList() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const jwtToken = localStorage.getItem('jwt_token');

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:5001/conversations', {
        headers: {
          'Authorization': `Bearer ${jwtToken}`
        }
      });
      
      const result = await response.json();
      setConversations(result.data.conversations);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteConversation = async (threadId: string) => {
    try {
      await fetch(`http://localhost:5001/conversations/${threadId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${jwtToken}`
        }
      });
      
      // Refresh list
      fetchConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const selectConversation = (threadId: string) => {
    // Navigate to chat with this thread_id
    // Pass thread_id to your chat component
    window.location.href = `/chat?thread_id=${threadId}`;
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="conversation-list">
      <h2>Your Conversations</h2>
      {conversations.map(conv => (
        <div key={conv.thread_id} className="conversation-item">
          <div onClick={() => selectConversation(conv.thread_id)}>
            <p className="last-message">{conv.last_message}</p>
            <p className="timestamp">
              {new Date(conv.updated_at).toLocaleDateString()}
            </p>
          </div>
          <button onClick={() => deleteConversation(conv.thread_id)}>
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}

export default ConversationList;
```

## Chat Component Example

```typescript
import React, { useState } from 'react';

function Chat({ initialThreadId = null }) {
  const [threadId, setThreadId] = useState(initialThreadId);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const jwtToken = localStorage.getItem('jwt_token');

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    const userQuery = input;
    setInput('');

    try {
      const response = await fetch('http://localhost:5001/query/sse', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: userQuery,
          thread_id: threadId,  // null for first message
          config: {}
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'chunk') {
              // Save thread_id from first response
              if (!threadId && data.thread_id) {
                setThreadId(data.thread_id);
              }
              assistantMessage = data.chunk;
            }
          }
        }
      }

      // Add assistant message to UI
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: assistantMessage 
      }]);

    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
      {threadId && <p className="thread-info">Thread: {threadId}</p>}
    </div>
  );
}

export default Chat;
```

## Important Notes

1. **Always store the `thread_id`** returned from the first query to continue the conversation
2. **Pass `thread_id: null`** or omit it for new conversations
3. **Conversations are automatically tracked** - you don't need to call any additional endpoint
4. **Use SSE endpoints** (`/query/sse` or `/query/stream_steps/sse`) - the Celery endpoint doesn't track conversations yet
5. **Handle authentication properly** - always include the JWT token in the Authorization header

## Pagination

For large conversation lists, use pagination:

```javascript
// Page 1 (first 20 conversations)
fetch('/conversations?limit=20&offset=0')

// Page 2 (next 20 conversations)
fetch('/conversations?limit=20&offset=20')

// Page 3
fetch('/conversations?limit=20&offset=40')
```

## Error Handling

```javascript
const response = await fetch('/conversations', {
  headers: { 'Authorization': `Bearer ${jwtToken}` }
});

const result = await response.json();

if (result.statusCode !== 200) {
  console.error('Error:', result.message);
  // Handle error (e.g., show error message to user)
} else {
  console.log('Success:', result.data);
}
```

## Common Status Codes

- `200` - Success
- `401` - Unauthorized (invalid or missing JWT token)
- `403` - Forbidden (trying to access another user's conversation)
- `404` - Not found (conversation doesn't exist)
- `500` - Server error
