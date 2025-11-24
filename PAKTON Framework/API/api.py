"""
Description: 
    FastAPI application providing REST endpoints for the PAKTON multi-agent framework.
    Supports asynchronous operations for interrogation, research, document indexing,
    and task status monitoring using Celery for background processing.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/02/09
"""

from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult
from sqlalchemy.orm import Session
from .tasks import celery_app
from .response_template import create_response
from .config import Config
from .auth import get_current_user, SupabaseUser
from .database import get_db, ConversationRepository
from typing import Dict, Any, Optional, List
from .logger import logger
import json
import asyncio

app = FastAPI(
    title="Multi Agent Framework Service API",
    description="API for requesting the Multi Agent Framework using FastAPI, Celery, Redis, RabbitMQ.",
    version="1.0.0",
    contact={
        "name": "Petros Raptopoulos",
        "email": "petrosrapto@gmail.com",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    """
    Interact with PAKTON using the Archivist agent.
    """
    query: str
    thread_id: Optional[str] = None
    config: Optional[dict] = {}

@app.post("/query/celery", tags=["Archivist Operations"])
async def process_query_celery(
    request: QueryRequest,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Process a query using the Archivist agent**

    This endpoint processes a query using the Archivist agent with optional thread ID for conversation continuity.
    Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Parameters:**
    - `query`: The user query to process
    - `thread_id`: Optional thread ID for conversation continuity
    - `config`: Optional configuration dictionary for model settings
        - `model`: The model's configuration to use
            - `API`: Optional string specifying the model's API
            - `model_id`: Optional string specifying the model ID

    **Response:**
    - Returns a **task_id** that can be used to track the query processing operation.

    **Example Request:**
    ```json
    {
        "query": "What is the weather like today?",
        "thread_id": "thread_123",
        "config": {
            "model": {
                "API": "openai",
                "model_id": "gpt-4o"
            }
        }
    }
    ```
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Processing Celery query request - User: {user_info}, Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    try:
        # Pass user email to the task so it can handle conversation tracking
        user_email = user.email if user and user.email else None
        
        task = celery_app.send_task(
            f'{Config.SERVICE_NAME}.tasks.process_query',
            args=[request.query, request.thread_id, request.config, user_email],
            queue=Config.SERVICE_QUEUE
        )
        logger.info(f"Celery task created successfully - Task ID: {task.id}")
        return create_response("Query processing started", 202, {"task_id": task.id})
    except Exception as e:
        logger.error(f"Failed to create Celery task: {str(e)}")
        return create_response("Failed to start query processing", 500, {"error": str(e)})

@app.post("/query/sse", tags=["Archivist Operations"])
async def process_query_sse(
    request: QueryRequest,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Process a query using the Archivist with Server-Sent Events (SSE)**

    This endpoint processes a query using the Archivist and streams the response in real-time
    using Server-Sent Events (SSE). Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Parameters:**
    - `query`: The user query to process
    - `thread_id`: Optional thread ID for conversation continuity
    - `config`: Optional configuration dictionary for model settings
        - `model`: The model's configuration to use
            - `API`: Optional string specifying the model's API
            - `model_id`: Optional string specifying the model ID

    **Response:**
    - Returns a streaming response with real-time updates
    - Events are sent as JSON data with the following structure:
      - `type`: "chunk" for partial data, "complete" for completion, "error" for errors
      - `thread_id`: The thread ID used for the conversation
      - `chunk`: The partial response data (only for "chunk" type)
      - `error`: Error message (only for "error" type)

    **Example Request:**
    ```json
    {
        "query": "What is the weather like today?",
        "thread_id": "thread_123",
        "config": {
            "model": {
                "API": "openai",
                "model_id": "gpt-4o"
            }
        }
    }
    ```

    **Example SSE Response:**
    ```
    data: {"type": "chunk", "thread_id": "thread_123", "chunk": {...}}

    data: {"type": "chunk", "thread_id": "thread_123", "chunk": {...}}

    data: {"type": "complete"}
    ```
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Processing SSE query request - User: {user_info}, Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    async def event_stream():
        try:
            logger.debug("Starting SSE event stream")
            # Import here to avoid circular imports
            from Archivist import Archivist
            
            async with Archivist() as archivist:
                logger.debug("Archivist initialized successfully")
                result = await archivist.process_query(request.query, request.thread_id, request.config)
                
                logger.info(f"Query processed successfully - Result: {result}")
                
                # Track conversation in database if user is authenticated
                if user and user.email:
                    try:
                        thread_id = result["thread_id"]
                        
                        # Get or create conversation
                        conversation = ConversationRepository.get_by_thread_id(db, thread_id)
                        if not conversation:
                            # Use the first 500 characters of the query as the title
                            title = request.query[:500] if len(request.query) <= 500 else request.query[:497] + "..."
                            ConversationRepository.create(
                                db=db,
                                thread_id=thread_id,
                                user_email=user.email,
                                title=title
                            )
                        
                        # Update message count and timestamp (count only human and AI messages)
                        messages = result['response']['messages']
                        message_count = ConversationRepository.count_human_and_ai_messages(messages)
                        ConversationRepository.update_message_count_and_timestamp(
                            db=db,
                            thread_id=thread_id,
                            message_count=message_count
                        )
                        
                        logger.info(f"Conversation tracked for user {user.email}, thread {thread_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to track conversation: {str(db_error)}")
                        # Continue despite database error
                
                # Format as SSE
                data = {
                    "type": "chunk",
                    "thread_id": result["thread_id"],
                    "chunk": result['response']['messages'][-1].content
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                logger.debug("SSE stream completed successfully")
                
        except Exception as e:
            logger.error(f"Error processing SSE query: {str(e)}", exc_info=True)
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

@app.post("/query/stream_steps/sse", tags=["Archivist Operations"])
async def process_query_stream_steps_sse(
    request: QueryRequest,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Process a query using Archivist with streaming intermediate steps via Server-Sent Events (SSE)**

    This endpoint processes a query using the Archivist and streams intermediate steps in real-time
    using Server-Sent Events (SSE). Unlike the regular SSE endpoint, this one shows the agent's
    thinking process and intermediate steps. Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Parameters:**
    - `query`: The user query to process
    - `thread_id`: Optional thread ID for conversation continuity
    - `config`: Optional configuration dictionary for model settings
        - `model`: The model's configuration to use
            - `API`: Optional string specifying the model's API
            - `model_id`: Optional string specifying the model ID

    **Response:**
    - Returns a streaming response with real-time updates of intermediate steps
    - Events are sent as JSON data with the following structure:
      - `type`: "step" for intermediate steps, "error" for errors
      - `thread_id`: The thread ID used for the conversation
      - `step`: The intermediate step data (only for "step" type)
      - `error`: Error message (only for "error" type)

    **Example Request:**
    ```json
    {
        "query": "What is the weather like today?",
        "thread_id": "thread_123",
        "config": {
            "model": {
                "API": "openai",
                "model_id": "gpt-4o"
            }
        }
    ```

    **Example SSE Response:**
    ```
    data: {"type": "step", "thread_id": "thread_123", "step": {...}}

    data: {"type": "step", "thread_id": "thread_123", "step": {...}}

    data: {"type": "complete"}
    ```
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Processing streaming steps SSE query request - User: {user_info}, Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    async def event_stream():
        try:
            logger.debug("Starting streaming steps SSE event stream")
            # Import here to avoid circular imports
            from Archivist import Archivist
            
            async with Archivist() as archivist:
                logger.debug("Archivist initialized successfully for streaming steps")
                
                response_thread_id = None
                all_chunks = []  # Store all chunks to count messages later
                
                async for result in archivist.process_query_stream(request.query, request.thread_id, request.config):
                    response_thread_id = result["thread_id"]
                    chunk = result["chunk"]
                    all_chunks.append(chunk)  # Store chunk for later counting
                    
                    # Handle different types of chunks based on the agent's output
                    if "messages" in chunk and chunk["messages"]:
                        last_message = chunk["messages"][-1]
                        # if hasattr(last_message, 'content') and last_message.content:
                        # Extract tool calls information if present
                        tool_calls = []
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                tool_call_info = {
                                    "name": tool_call.get('name', ''),
                                    "arguments": tool_call.get('args', {})
                                }
                                tool_calls.append(tool_call_info)
                        

                        # Send intermediate step
                        step_data = {
                            "type": "step",
                            "thread_id": response_thread_id,
                            "step": {
                                "content": last_message.content if hasattr(last_message, 'content') and last_message.content else "",
                                "message_type": getattr(last_message, 'type', 'unknown'),
                                "timestamp": asyncio.get_event_loop().time(),
                                "tool_calls": tool_calls,
                                "artifact": last_message.artifact if hasattr(last_message, 'artifact') and last_message.artifact else ""
                            }
                        }
                        yield f"data: {json.dumps(step_data)}\n\n"
                
                # Track conversation in database after streaming completes
                if user and user.email and response_thread_id:
                    try:
                        # Get or create conversation
                        conversation = ConversationRepository.get_by_thread_id(db, response_thread_id)
                        if not conversation:
                            # Use the first 500 characters of the query as the title
                            title = request.query[:500] if len(request.query) <= 500 else request.query[:497] + "..."
                            ConversationRepository.create(
                                db=db,
                                thread_id=response_thread_id,
                                user_email=user.email,
                                title=title
                            )
                        
                        # Update message count and timestamp (count only human and AI messages)
                        # Extract all messages from collected chunks
                        all_messages = []
                        for chunk in all_chunks:
                            if "messages" in chunk and chunk["messages"]:
                                all_messages.extend(chunk["messages"])
                        
                        # Count only human and AI messages
                        message_count = ConversationRepository.count_human_and_ai_messages(all_messages)
                        ConversationRepository.update_message_count_and_timestamp(
                            db=db,
                            thread_id=response_thread_id,
                            message_count=message_count
                        )
                        
                        logger.info(f"Conversation tracked for user {user.email}, thread {response_thread_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to track conversation: {str(db_error)}")
                        # Continue despite database error
            
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                logger.debug("Streaming steps SSE stream completed successfully")
                
        except Exception as e:
            logger.error(f"Error processing streaming steps SSE query: {str(e)}", exc_info=True)
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

@app.post("/index/document/", tags=["Archivist Operations"])
async def index_document(
    metadata: str = Form(...),
    file: UploadFile = File(...),
    user: Optional[SupabaseUser] = Depends(get_current_user)
):
    """
    **Index a document with metadata**

    This endpoint accepts a file and its associated metadata for indexing.
    Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Format:** `multipart/form-data`
    
    **Parameters:**
    - `metadata` (Form field): JSON string containing document metadata
    - `file` (File): The document to be indexed

    **Request Body Example:**
    ```json
    {
        "metadata": {
            "title": "Sample Document",
            "author": "John Doe",
            "date": "2025-02-15",
            "tags": ["report", "technical"]
        },
        "file": <binary_file_content>
    }
    ```

    **Response:**
    - Returns a **task_id** that can be used to track the indexing operation.
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Indexing document - User: {user_info}, File: {file.filename}")
    
    try:
        # Parse the metadata string into a dictionary
        metadata_dict = json.loads(metadata)
        
        # Add filename to metadata
        metadata_dict['filename'] = file.filename

        # Read the file content
        file_content = await file.read()
        
        task = celery_app.send_task(
            f'{Config.SERVICE_NAME}.tasks.index_document',
            args=[file_content, metadata_dict],
            queue=Config.SERVICE_QUEUE
        )
        return create_response("Indexing operation started", 202, {"task_id": task.id})
    
    except json.JSONDecodeError:
        return create_response("Invalid metadata format", 400, {"error": "Metadata must be a valid JSON string"})
    except Exception as e:
        return create_response("Error processing request", 500, {"error": str(e)})

class ResearchRequest(BaseModel):
    """
    Request PAKTON for research operation using the Researcher agent.
    """
    query: str
    instructions: str = ""
    agent_config: Optional[Dict[str, Any]] = None
    search_config: Optional[Dict[str, Any]] = None

@app.post("/research/", tags=["Researcher Operations"])
async def research(
    request: ResearchRequest,
    user: Optional[SupabaseUser] = Depends(get_current_user)
):
    """
    **Execute a research operation**

    This endpoint processes a research query using the Researcher agent.
    Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Parameters:**
    - `query`: The search query to research
    - `instructions`: Optional instructions for the researcher agent
    - `agent_config`: Optional configuration for the Researcher agent initialization
    - `search_config`: Optional configuration for the search operation

    **Response:**
    - Returns a **task_id** that can be used to track the research operation.
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Research request - User: {user_info}, Query: {request.query}")
    
    task = celery_app.send_task(
        f'{Config.SERVICE_NAME}.tasks.research',
        args=[request.query, request.instructions, request.agent_config, request.search_config],
        queue=Config.SERVICE_QUEUE
    )
    return create_response("Research operation started", 202, {"task_id": task.id})

class InterrogationRequest(BaseModel):
    """
    Request PAKTON for interrogation operation using the Interrogator agent.
    """
    userQuery: str
    userContext: str = ""
    userInstructions: str = ""

@app.post("/interrogation/", tags=["Interrogator Operations"])
async def interrogation(
    request: InterrogationRequest,
    user: Optional[SupabaseUser] = Depends(get_current_user)
):
    """
    **Execute an interrogation operation**

    This endpoint processes an interrogation query using the Interrogator agent.
    Requires authentication.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Request Parameters:**
    - `userQuery`: The user's query to interrogate
    - `userContext`: Optional context for the interrogation
    - `userInstructions`: Optional instructions for the interrogator agent

    **Response:**
    - Returns a **task_id** that can be used to track the interrogation operation.
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Interrogation request - User: {user_info}, Query: {request.userQuery}")
    
    task = celery_app.send_task(
        f'{Config.SERVICE_NAME}.tasks.interrogation',
        args=[request.userQuery, request.userContext, request.userInstructions],
        queue=Config.SERVICE_QUEUE
    )
    return create_response("Interrogation operation started", 202, {"task_id": task.id})

@app.get("/task_status/{task_id}", tags=["Task Management"])
async def get_task_status(
    task_id: str,
    user: Optional[SupabaseUser] = Depends(get_current_user)
):
    """
    **Check the status of an asynchronous task**

    Requires authentication to prevent unauthorized access to task results.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Example Call:**
    ```
    GET /task_status/06c21d13-ed66-44f9-a55e-43020e538bbd
    ```

    **Possible Task Statuses:**
    - `"PENDING"` → Task received but not started.
    - `"STARTED"` → Task is currently executing.
    - `"SUCCESS"` → Task completed successfully.
    - `"FAILURE"` → Task failed.
    - `"RETRY"` → Task is being retried.
    - `"REVOKED"` → Task was canceled before completion.

    **Response Example:**
    ```json
    {
        "task_id": "06c21d13-ed66-44f9-a55e-43020e538bbd",
        "task_status": "SUCCESS",
        "task_response": { "message": "File deleted successfully" }
    }
    ```
    """
    user_info = f"{user.email} ({user.user_id})" if user else "anonymous (auth disabled)"
    logger.info(f"Task status check - User: {user_info}, Task ID: {task_id}")

    task_result = AsyncResult(task_id, app=celery_app)
    return create_response(
        "Task status retrieved", 200,
        {
            "task_id": task_id,
            "task_status": task_result.status,  
            "task_response": task_result.result if task_result.ready() else None
        }
    )

@app.get("/conversations", tags=["Conversation Management"])
async def get_user_conversations(
    limit: Optional[int] = 50,
    offset: int = 0,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get all conversations for the authenticated user**

    Retrieves a list of conversations associated with the authenticated user,
    ordered by most recently updated first.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Query Parameters:**
    - `limit`: Maximum number of conversations to return (default: 50)
    - `offset`: Number of conversations to skip for pagination (default: 0)

    **Response Example:**
    ```json
    {
        "message": "Conversations retrieved successfully",
        "statusCode": 200,
        "data": {
            "conversations": [
                {
                    "thread_id": "thread_123",
                    "user_email": "user@example.com",
                    "title": "Weather Discussion",
                    "last_message": "The weather is sunny today...",
                    "created_at": "2025-11-23T10:00:00",
                    "updated_at": "2025-11-23T12:30:00"
                }
            ],
            "total": 10,
            "limit": 50,
            "offset": 0
        }
    }
    ```
    """
    if not user or not user.email:
        return create_response("Authentication required", 401, {})
    
    user_info = f"{user.email} ({user.user_id})"
    logger.info(f"Fetching conversations for user: {user_info}")
    
    try:
        conversations = ConversationRepository.get_by_user_email(
            db, user.email, limit=limit, offset=offset
        )
        total = ConversationRepository.count_by_user(db, user.email)
        
        return create_response(
            "Conversations retrieved successfully",
            200,
            {
                "conversations": [conv.to_dict() for conv in conversations],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        return create_response("Failed to retrieve conversations", 500, {"error": str(e)})

@app.get("/conversations/{thread_id}", tags=["Conversation Management"])
async def get_conversation(
    thread_id: str,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get a specific conversation by thread ID**

    Retrieves details of a specific conversation. Users can only access their own conversations.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Response Example:**
    ```json
    {
        "message": "Conversation retrieved successfully",
        "statusCode": 200,
        "data": {
            "thread_id": "thread_123",
            "user_email": "user@example.com",
            "title": "Weather Discussion",
            "last_message": "The weather is sunny today...",
            "created_at": "2025-11-23T10:00:00",
            "updated_at": "2025-11-23T12:30:00"
        }
    }
    ```
    """
    if not user or not user.email:
        return create_response("Authentication required", 401, {})
    
    logger.info(f"Fetching conversation {thread_id} for user {user.email}")
    
    try:
        conversation = ConversationRepository.get_by_thread_id(db, thread_id)
        
        if not conversation:
            return create_response("Conversation not found", 404, {})
        
        # Verify the conversation belongs to the user
        if conversation.user_email != user.email:
            return create_response("Access denied", 403, {})
        
        return create_response(
            "Conversation retrieved successfully",
            200,
            conversation.to_dict()
        )
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        return create_response("Failed to retrieve conversation", 500, {"error": str(e)})

@app.get("/conversations/{thread_id}/messages", tags=["Conversation Management"])
async def get_conversation_messages(
    thread_id: str,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get conversation messages by thread ID**

    Retrieves the full message history of a specific conversation thread.
    Users can only access their own conversations.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Response Example:**
    ```json
    {
        "message": "Conversation messages retrieved successfully",
        "statusCode": 200,
        "data": {
            "thread_id": "thread_123",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the weather like?"
                },
                {
                    "role": "assistant",
                    "content": "The weather is sunny today.",
                    "timelineItems": [...]
                }
            ]
        }
    }
    ```
    """
    if not user or not user.email:
        return create_response("Authentication required", 401, {})
    
    logger.info(f"Fetching conversation messages for thread {thread_id}, user {user.email}")
    
    try:
        # First verify the conversation exists and belongs to the user
        conversation = ConversationRepository.get_by_thread_id(db, thread_id)
        
        if not conversation:
            return create_response("Conversation not found", 404, {})
        
        # Verify the conversation belongs to the user
        if conversation.user_email != user.email:
            return create_response("Access denied", 403, {})
        
        # Get the conversation messages from Archivist checkpointer
        from Archivist import Archivist
        
        async with Archivist() as archivist:
            messages = await archivist.get_conversation_content(thread_id)
        
        return create_response(
            "Conversation messages retrieved successfully",
            200,
            {
                "thread_id": thread_id,
                "messages": messages
            }
        )
    except ValueError as e:
        logger.error(f"Invalid thread_id: {str(e)}")
        return create_response("Invalid thread ID", 400, {"error": str(e)})
    except RuntimeError as e:
        logger.error(f"Configuration error: {str(e)}")
        return create_response("Service configuration error", 500, {"error": str(e)})
    except Exception as e:
        logger.error(f"Error retrieving conversation messages: {str(e)}")
        return create_response("Failed to retrieve conversation messages", 500, {"error": str(e)})

@app.delete("/conversations/{thread_id}", tags=["Conversation Management"])
async def delete_conversation(
    thread_id: str,
    user: Optional[SupabaseUser] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Delete a conversation**

    Deletes a specific conversation. Users can only delete their own conversations.
    Note: This only deletes the conversation record, not the actual messages in the
    checkpoint database.

    **Authentication:**
    - Requires a valid Supabase JWT token in the Authorization header
    - Format: `Authorization: Bearer <token>`

    **Response Example:**
    ```json
    {
        "message": "Conversation deleted successfully",
        "statusCode": 200,
        "data": {}
    }
    ```
    """
    if not user or not user.email:
        return create_response("Authentication required", 401, {})
    
    logger.info(f"Deleting conversation {thread_id} for user {user.email}")
    
    try:
        conversation = ConversationRepository.get_by_thread_id(db, thread_id)
        
        if not conversation:
            return create_response("Conversation not found", 404, {})
        
        # Verify the conversation belongs to the user
        if conversation.user_email != user.email:
            return create_response("Access denied", 403, {})
        
        ConversationRepository.delete(db, thread_id)
        
        return create_response("Conversation deleted successfully", 200, {})
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return create_response("Failed to delete conversation", 500, {"error": str(e)})

@app.get("/health", tags=["Health Check"])
def health_check():
    """
    **Health Check Endpoint**

    This endpoint is used to check the health of the API service.

    **Response:**
    - Returns a 200 status code with a message indicating the service is healthy.
    """
    return {"status": "healthy"}

@app.get("/", tags=["Root"])
def root():
    """
    **Root Endpoint**

    Welcome message for the Service API.
    """
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the API of PAKTON",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Example of the content of the reply of the /task_status/{task_id} endpoint:
# {'message': 'Task status retrieved', 'statusCode': 200, 'data': {'task_id': '84fe0546-786e-4190-86bb-491980a0a0e1', 'task_status': 'SUCCESS', 'task_response': {'status': 'SUCCESS', 'task_id': '84fe0546-786e-4190-86bb-491980a0a0e1', 'message': 'File existence check completed', 'data': {'exists': False}}}}

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application shutdown initiated")