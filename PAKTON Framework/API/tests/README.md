# API Test Scripts

This directory contains test scripts for validating the API endpoints of the PAKTON Framework.

> **⚠️ Important**: These tests assume **authentication is DISABLED**. Set `ENABLE_AUTHENTICATION=false` in your API's `.env` file before running tests.

## Overview

The test suite includes:
- **`test_api_calls.py`**: Tests for Celery-based asynchronous endpoints (`/query/celery`, `/interrogation/`, `/research/`, `/index/document/`)
- **`test_query_sse.py`**: Tests for Server-Sent Events (SSE) streaming endpoint (`/query/sse`)
- **`demo_frontend/`**: Interactive React-based chat interface for quickly testing the `/query/sse` endpoint with a beautiful UI

## Prerequisites

### 1. Running API Service

Ensure the API service is running before executing any test scripts. The default base URL is `http://localhost:5001`.

**Configure Authentication** (Required for Tests):

These tests are designed to run **without authentication**. Before running tests, ensure authentication is disabled:

```bash
# In your API's .env file:
ENABLE_AUTHENTICATION=false
```

If authentication is enabled, all test requests will fail with 401 Unauthorized errors.

To start the API service:
```bash
cd /Users/petrosrapto/Desktop/PAKTON/PAKTON/PAKTON\ Framework/API
docker-compose up -d --build
```

### 2. Python Virtual Environment

It is **essential** to create a virtual environment to isolate test dependencies and avoid conflicts with system packages.

#### Create Virtual Environment

```bash
# Navigate to the tests directory
cd /Users/petrosrapto/Desktop/PAKTON/PAKTON/PAKTON\ Framework/API/tests

# Create virtual environment
python3 -m venv venv
```

#### Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

After activating the virtual environment, install the required packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `requests`: For synchronous HTTP requests (used in `test_api_calls.py`)
- `aiohttp`: For asynchronous HTTP and SSE streaming (used in `test_query_sse.py`)

## Demo Frontend (Quick Testing)

For a faster and more interactive way to test the `/query/sse` endpoint, use the included React-based chat frontend:

```bash
# Navigate to the demo frontend directory
cd demo_frontend

# Make the start script executable
chmod +x start.sh

# Run the frontend
./start.sh
```

The frontend will be available at **http://localhost:3012** and provides:
- 💬 Chat-like interface for testing queries
- 🧵 Thread ID management (optional input field)
- 🔄 Real-time SSE streaming visualization
- 🎨 Modern, beautiful UI with animations
- 📊 Connection status indicators

This is the **fastest way** to test and interact with the API's query endpoint. For more details, see [demo_frontend/README.md](demo_frontend/README.md).

## Test Scripts

### 1. `test_api_calls.py`

Tests Celery-based asynchronous endpoints that return task IDs for long-running operations.

#### Available Functions:

- **`poll_task_status(task_id)`**: Polls a Celery task until completion with exponential backoff
- **`interrogation()`**: Tests the `/interrogation/` endpoint for hypothesis evaluation
- **`index_document(file_path)`**: Tests the `/index/document/` endpoint for document indexing
- **`research()`**: Tests the `/research/` endpoint for document search and retrieval
- **`process_query(query, thread_id)`**: Tests the `/query/celery` endpoint for conversational queries
- **`check_health()`**: Tests the `/health` endpoint
- **`check_root()`**: Tests the root `/` endpoint

#### Usage:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the test script
python test_api_calls.py
```

#### Customize Tests:

Edit the `__main__` block in `test_api_calls.py` to enable/disable specific tests:

```python
if __name__ == "__main__":
    # Example: Test query endpoint
    poll_task_status(process_query("Ok, what can you do for me? Give me an overview.", "12"))
    
    # Example: Test document indexing
    # poll_task_status(index_document("example_0.docx"))
    
    # Example: Test interrogation
    # poll_task_status(interrogation())
    
    # Example: Test research
    # poll_task_status(research())
```

### 2. `test_query_sse.py`

Tests the Server-Sent Events (SSE) streaming endpoint for real-time query responses.

#### Available Functions:

- **`test_query_sse(query, thread_id)`**: Tests the `/query/sse` endpoint with streaming response handling

#### Usage:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the test script
python test_query_sse.py
```

#### Test Cases Included:

1. Simple query without thread ID (new conversation)
2. Follow-up query with existing thread ID (conversation continuity)
3. New query with new thread
4. Query with specific thread ID

#### Customize Tests:

Edit the `main()` function in `test_query_sse.py`:

```python
async def main():
    # Test 1: New conversation
    query1 = "Your custom query here"
    thread_id = await test_query_sse(query1)
    
    # Test 2: Follow-up with thread context
    if thread_id:
        query2 = "Follow-up question"
        await test_query_sse(query2, thread_id)
```

## Configuration

### Base URL

Both test scripts use `BASE_URL = "http://localhost:5001"` by default. To test against a different server:

**Option 1: Edit the scripts**
```python
BASE_URL = "http://your-server-address:port"
```

**Option 2: Environment variable** (requires script modification)
```bash
export API_BASE_URL="http://your-server-address:port"
```

## Example Workflow

```bash
# 1. Start the API service
cd /Users/petrosrapto/Desktop/PAKTON/PAKTON/PAKTON\ Framework/API
docker-compose up -d --build

# 2. Navigate to tests directory
cd tests

# 3. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run Celery endpoint tests
python test_api_calls.py

# 6. Run SSE streaming tests
python test_query_sse.py

# 7. Deactivate virtual environment when done
deactivate
```

## Troubleshooting

### Connection Refused
- Ensure the API service is running: `docker-compose ps`
- Check if the service is listening on port 5001: `lsof -i :5001`

### Import Errors
- Verify virtual environment is activated: `which python` should point to `venv/bin/python`
- Reinstall dependencies: `pip install -r requirements.txt`

### Task Timeout
- Increase `max_retries` or `initial_interval` in `poll_task_status()`
- Check Celery worker logs: `docker-compose logs -f worker`

### SSE Stream Errors
- Ensure `aiohttp` is installed: `pip list | grep aiohttp`
- Check API logs for streaming errors

## Notes

- **Virtual environment is essential** to avoid dependency conflicts
- Always activate the virtual environment before running tests
- The `requirements.txt` must be installed for tests to work properly
- SSE tests require `aiohttp` for async streaming support
- Celery tests use `requests` for synchronous HTTP calls with polling

## Author

Raptopoulos Petros [petrosrapto@gmail.com]  
Date: 2025/03/10
