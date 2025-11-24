"""
Description: 
    Celery task definitions for asynchronous processing of PAKTON framework operations.
    Includes tasks for interrogation, research, and document indexing with retry logic
    and error handling for distributed task execution.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

from .config import Config
from celery import Celery
import asyncio
import os
import tempfile
import traceback
from .response_template import create_task_response
from .database import get_db_session, ConversationRepository

from .logger import logger
logger.info("Celery Worker initialized.")

# Initialize Celery
celery_app = Celery(
    Config.SERVICE_NAME,
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = Config.TASK_ROUTES

# Ensure Celery does not override the root logger and uses the custom log format
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"
celery_app.conf.worker_task_log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s"

# Global Archivist instance - initialized once per worker
archivist = None

def get_archivist():
    """Get or create the global Archivist instance"""
    global archivist
    if archivist is None:
        from Archivist import Archivist
        archivist = Archivist()
        logger.info("Archivist instance created")
    return archivist

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.interrogation', bind=True, default_retry_delay=5, max_retries=3)
def async_interrogation(self, userQuery: str, userContext: str = "", userInstructions: str = ""):
    """Asynchronous interrogation for given query."""
    logger.debug(f"Task started: async_interrogation - userQuery: {userQuery}, userContext: {userContext}, userInstructions: {userInstructions}")
    try:
        from Interrogator import Interrogator

        interrogator = Interrogator(config = {"run_name": "Example Interrogation"})
        results = interrogator.interrogation(userQuery=userQuery, userContext=userContext, userInstructions=userInstructions)
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Interrogation completed",
            data={"report": results["report"], "conclusion": results["conclusion"]}
        )
    except Exception as e:
        logger.error(f"Error in async_interrogation: {e}")

        if self.request.retries < self.max_retries:  # Check retry limit
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)  # Retry after 5 seconds

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to interrogate: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.process_query', bind=True, default_retry_delay=5, max_retries=3)
def async_process_query(self, query: str, thread_id: str = None, config: dict = None, user_email: str = None):
    """
    Asynchronous query processing using Archivist.

    Args:
        query (str): The user query to process.
        thread_id (str, optional): Thread ID for conversation continuity.
        config (dict, optional): Configuration dictionary containing model/agent settings.
        user_email (str, optional): User's email for conversation tracking.

    Returns:
        dict: JSON response with query result.

        **Success Response:**
        ```json
        {
            "status": "SUCCESS",
            "task_id": "<celery_task_id>",
            "message": "Query processed successfully",
            "data": {
                "thread_id": "<thread_id>",
                "response": "<response_content>",
                "messages": [...]
            }
        }
        ```

        **Failure Response:**
        ```json
        {
            "status": "FAILURE",
            "task_id": "<celery_task_id>",
            "message": "Failed to process query: <error_message>"
        }
        ```
    """
    logger.debug(f"Task started: async_process_query - query: {query}, thread_id: {thread_id}, user_email: {user_email}")
    
    try:
        archivist = get_archivist()
        
        async def process_query_async():
            async with archivist:
                result = await archivist.process_query(query, thread_id, config)
                logger.debug(f"Task completed: process_query_async - result: {result}")
                return result
        
        # Run the async function synchronously
        result = asyncio.run(process_query_async())

        logger.debug(f"Task completed: async_process_query run - result: {result}")
        
        # Track conversation in database if user is authenticated
        if user_email and result.get('thread_id'):
            try:
                with get_db_session() as db:
                    thread_id = result['thread_id']
                    
                    # Get or create conversation
                    conversation = ConversationRepository.get_by_thread_id(db, thread_id)
                    if not conversation:
                        # Use the first 500 characters of the query as the title
                        title = query[:500] if len(query) <= 500 else query[:497] + "..."
                        ConversationRepository.create(
                            db=db,
                            thread_id=thread_id,
                            user_email=user_email,
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
                    
                    logger.info(f"Conversation tracked for user {user_email}, thread {thread_id}")
            except Exception as db_error:
                logger.error(f"Failed to track conversation: {str(db_error)}")
                # Continue despite database error
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Query processed successfully",
            data={
                "thread_id": result['thread_id'],
                "response_content": result['response']['messages'][-1].content,
            }
        )
        
    except Exception as e:
        logger.error(f"Error in async_process_query: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to process query: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.index_document', bind=True, default_retry_delay=5, max_retries=3)
def async_index_document(self, file_content: bytes, metadata: dict):
    """
    Asynchronous indexing of a document using Archivist.

    Args:
        file_content (bytes): The binary content of the document.
        metadata (dict): Metadata including the filename.

    Returns:
        dict: JSON response indicating indexing status.

        **Success Response:**
        ```json
        {
            "status": "SUCCESS",
            "task_id": "<celery_task_id>",
            "message": "Indexing Document completed"
        }
        ```

        **Failure Response:**
        ```json
        {
            "status": "FAILURE",
            "task_id": "<celery_task_id>",
            "message": "Failed to index document: <error_message>"
        }
        ```
    """
    logger.debug(f"Task started: index_document - metadata: {metadata}")
    try:
        from Archivist import Archivist

        archivist = Archivist(config = {"enable_vectordb": True, "run_name": "Example Index"})
        # Validate filename exists in metadata
        if 'filename' not in metadata:
            raise ValueError("Filename must be provided in metadata")
        
        filename = metadata['filename']
        file_extension = os.path.splitext(filename)[-1].lower()

        if file_extension not in ['.docx', '.pdf', '.txt']:
            raise ValueError("Unsupported file type. Only .docx , .pdf and .txt are allowed.")

        fd, temp_file_path = tempfile.mkstemp(suffix=file_extension)

        try:
            
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(file_content)
                temp_file.flush()  # Ensure file is written to disk before using it
                logger.info(f"Temporary file created: {temp_file_path}")

                archivist.index(filePath=temp_file_path)

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Temporary file deleted: {temp_file_path}")

        logger.info(f"Indexing complete for matadata: {metadata}")
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Indexing Document completed"
        )
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=str(ve)
        )
    except Exception as e:
        logger.error(f"Error in index_document: {e}")

        if self.request.retries < self.max_retries:  
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5) 
        
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to index document: {e}"
        )

@celery_app.task(name=f'{Config.SERVICE_NAME}.tasks.research', bind=True, default_retry_delay=5, max_retries=3)
def async_research(self, query: str, instructions: str = "", agent_config: dict = None, search_config: dict = None):
    """Asynchronous research for given query using the Researcher agent."""
    logger.debug(f"Task started: async_research - query: {query}, instructions: {instructions}, agent_config: {agent_config}, search_config: {search_config}")
    try:
        from Researcher import Researcher

        researcher = Researcher(config=agent_config or {})
        results = researcher.search(query=query, instructions=instructions, config=search_config or {})
        
        # Convert Document objects to dictionaries
        chunks = []
        if search_config and search_config.get("return_chunks", False) and "responseContext" in results:
            for doc in results.get("responseContext", []):
                # Extract the page_content and metadata from each Document
                if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                    chunks.append({
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    })
                else:
                    # If the structure is different, try to convert the entire object to dict
                    try:
                        chunks.append(dict(doc))
                    except (TypeError, ValueError):
                        # Last resort: convert to string
                        chunks.append({"content": str(doc)})
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Research completed",
            data={"response": results.get("response", ""), "chunks": chunks}
        )
    except Exception as e:
        logger.error(f"Error in async_research: {e}")

        if self.request.retries < self.max_retries:  # Check retry limit
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)  # Retry after 5 seconds

        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to research: {e}"
        )

# Celery worker startup hook
@celery_app.on_after_configure.connect
def setup_worker_initialization(sender, **kwargs):
    """Initialize the archivist instance when a worker starts"""
    logger.info("Setting up worker initialization...")
    try:
        get_archivist()
        logger.info("Worker initialized successfully with archivist instance")
    except Exception as e:
        logger.error(f"Failed to initialize worker: {e}")