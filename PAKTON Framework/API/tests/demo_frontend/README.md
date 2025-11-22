# PAKTON API Chat Frontend

A React-based chat interface for testing the PAKTON API `/query/sse` endpoint with real-time streaming responses using Server-Sent Events (SSE).

## Features

- 💬 Chat-like interface for querying the API
- 🔄 Real-time streaming responses via SSE
- 🧵 Thread ID management for conversation continuity
- 🎨 Clean and responsive UI
- 📊 Connection status indicators
- 🔧 Easy to test and debug API responses

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- PAKTON API server running on `http://localhost:5001`

## Installation

1. Navigate to the demo_frontend directory:
```bash
cd "PAKTON Framework/API/tests/demo_frontend"
```

2. Install dependencies:
```bash
npm install
```

## Usage

### Using the start script (recommended):

```bash
chmod +x start.sh
./start.sh
```

### Manual start:

```bash
npm start
```

The application will open automatically at `http://localhost:3012`.

## How to Use

1. **Thread ID Field**: 
   - Leave empty to create a new conversation thread
   - Enter an existing thread ID to continue a previous conversation
   - The thread ID is automatically populated after the first message

2. **Chat Input**:
   - Type your query in the text area
   - Press Enter to send (Shift+Enter for new line)
   - Click "Send" button

3. **Clear Chat**:
   - Click "Clear Chat" to reset the conversation and thread ID

4. **Connection Status**:
   - **Ready**: Idle, ready to send messages
   - **Connecting**: Establishing connection to API
   - **Streaming**: Receiving response from API
   - **Connection Error**: Failed to connect or error occurred

## API Endpoint

This frontend is configured to test the `/query/sse` endpoint:

- **URL**: `http://localhost:5001/query/sse`
- **Method**: POST
- **Headers**: 
  - `Content-Type: application/json`
  - `Accept: text/event-stream`
- **Body**:
```json
{
  "query": "Your question here",
  "thread_id": "optional-thread-id"
}
```

## Response Format

The API returns Server-Sent Events with the following data types:

- `chunk`: Streaming response chunks
- `complete`: Stream completion signal
- `error`: Error information

## Troubleshooting

### API Connection Issues

Make sure the PAKTON API server is running on `http://localhost:5001`:

```bash
cd "PAKTON Framework/API"
docker-compose up -d --build
```

### Port Already in Use

If port 3012 is already in use, you can change it in `package.json`:

```json
"scripts": {
  "start": "PORT=3013 react-scripts start"
}
```

## Development

- Built with React 18
- Uses Server-Sent Events (SSE) for real-time streaming
- Responsive design with mobile support
- No external UI libraries for simplicity

## Author

Raptopoulos Petros [petrosrapto@gmail.com]

## Date

2025/03/10
