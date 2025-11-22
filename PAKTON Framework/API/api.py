"""
Description: 
    FastAPI application providing REST endpoints for the PAKTON multi-agent framework.
    Supports asynchronous operations for interrogation, research, document indexing,
    and task status monitoring using Celery for background processing.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/02/09
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult
from .tasks import celery_app
from .response_template import create_response
from .config import Config
from typing import Dict, Any, Optional
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
async def process_query_celery(request: QueryRequest):
    """
    **Process a query using the Archivist agent**

    This endpoint processes a query using the Archivist agent with optional thread ID for conversation continuity.

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
    logger.info(f"Processing Celery query request - Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    try:
        task = celery_app.send_task(
            f'{Config.SERVICE_NAME}.tasks.process_query',
            args=[request.query, request.thread_id, request.config],
            queue=Config.SERVICE_QUEUE
        )
        logger.info(f"Celery task created successfully - Task ID: {task.id}")
        return create_response("Query processing started", 202, {"task_id": task.id})
    except Exception as e:
        logger.error(f"Failed to create Celery task: {str(e)}")
        return create_response("Failed to start query processing", 500, {"error": str(e)})

@app.post("/query/sse", tags=["Archivist Operations"])
async def process_query_sse(request: QueryRequest):
    """
    **Process a query using the Archivist with Server-Sent Events (SSE)**

    This endpoint processes a query using the Archivist and streams the response in real-time
    using Server-Sent Events (SSE).

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
    logger.info(f"Processing SSE query request - Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    async def event_stream():
        try:
            logger.debug("Starting SSE event stream")
            # Import here to avoid circular imports
            from Archivist import Archivist
            
            async with Archivist() as archivist:
                logger.debug("Archivist initialized successfully")
                result = await archivist.process_query(request.query, request.thread_id, request.config)
                
                logger.info(f"Query processed successfully - Result: {result}")
                
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
async def process_query_stream_steps_sse(request: QueryRequest):
    """
    **Process a query using Archivist with streaming intermediate steps via Server-Sent Events (SSE)**

    This endpoint processes a query using the Archivist and streams intermediate steps in real-time
    using Server-Sent Events (SSE). Unlike the regular SSE endpoint, this one shows the agent's
    thinking process and intermediate steps.

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
    logger.info(f"Processing streaming steps SSE query request - Query length: {len(request.query)}, Thread ID: {request.thread_id}")
    
    async def event_stream():
        try:
            logger.debug("Starting streaming steps SSE event stream")
            # Import here to avoid circular imports
            from Archivist import Archivist
            
            async with Archivist() as archivist:
                logger.debug("Archivist initialized successfully for streaming steps")
                
                response_thread_id = None
                
                async for result in archivist.process_query_stream(request.query, request.thread_id, request.config):
                    response_thread_id = result["thread_id"]
                    chunk = result["chunk"]
                    
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
    file: UploadFile = File(...)
):
    """
    **Index a document with metadata**

    This endpoint accepts a file and its associated metadata for indexing.

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
async def research(request: ResearchRequest):
    """
    **Execute a research operation**

    This endpoint processes a research query using the Researcher agent.

    **Request Parameters:**
    - `query`: The search query to research
    - `instructions`: Optional instructions for the researcher agent
    - `agent_config`: Optional configuration for the Researcher agent initialization
    - `search_config`: Optional configuration for the search operation

    **Response:**
    - Returns a **task_id** that can be used to track the research operation.
    """
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
async def interrogation(request: InterrogationRequest):

    task = celery_app.send_task(
        f'{Config.SERVICE_NAME}.tasks.interrogation',
        args=[request.userQuery, request.userContext, request.userInstructions],
        queue=Config.SERVICE_QUEUE
    )
    return create_response("Interrogation operation started", 202, {"task_id": task.id})

@app.get("/task_status/{task_id}", tags=["Task Management"])
async def get_task_status(task_id: str):
    """
    **Check the status of an asynchronous task**

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

    task_result = AsyncResult(task_id, app=celery_app)
    return create_response(
        "Task status retrieved", 200,
        {
            "task_id": task_id,
            "task_status": task_result.status,  
            "task_response": task_result.result if task_result.ready() else None
        }
    )

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