"""
Description:
Main Archivist agent implementation. Provides the core agent class for indexing documents
using various indexer backends (VectorDB, LightRAG) and managing the graph-based workflow.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import traceback
from typing import Dict, Any, List, Optional, AsyncGenerator

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import time
import uuid
from Archivist.graph import GraphBuilder
from Archivist.indexers import VectorDBIndexer, LightRAGIndexer
from Archivist.tools import create_interrogation_tool

from Archivist.utils import config, logger, ARCHIVIST_SYSTEM_PROMPT, get_required_env
from Archivist.models import get_llm

from contextlib import AsyncExitStack

class Archivist:
    """Archivist agent for indexing information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Archivist agent.
        
        Args:
            config: Configuration for the agent
        """
        try:
            self.config = config or {}
            self.graph_builder = GraphBuilder()
            self.graph = None
            
            logger.info("Initializing Archivist with config: %s", self.config)

            self._setup_indexers()

            # Build and compile the graph
            self._build_graph()

            self.exit_stack = AsyncExitStack()

            self.checkpointer: Optional[AsyncPostgresSaver] = None
            self._conn_string: Optional[str] = None
            
            # Initialize tools
            self.tools = []
            self._setup_tools()

        except Exception as e:
            logger.error("Error initializing Archivist: %s", str(e))
            logger.debug(traceback.format_exc())
    
    async def __aenter__(self):
        await self._setup_postgres_checkpointer()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    def _setup_tools(self):
        """Set up the tools available to the agent."""
        try:
            logger.info("Setting up tools...")
            
            # Add interrogation tool if enabled
            if self.config.get("enable_interrogation_tool", True):
                try:
                    interrogation_config = self.config.get("interrogation_config", {})
                    interrogation_tool = create_interrogation_tool(config=interrogation_config)
                    self.tools.append(interrogation_tool)
                    logger.info("Interrogation tool added successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize Interrogation tool: {str(e)}")
                    logger.debug(traceback.format_exc())
            
            logger.info(f"Total tools available: {len(self.tools)}")
            
        except Exception as e:
            logger.error(f"Error in setting up tools: {str(e)}")
            logger.debug(traceback.format_exc())

    def _setup_indexers(self):
        """Set up the indexers components."""
        try:
            logger.info("Setting up indexers...")

            # Vector DB indexer
            if self.config.get("enable_vectordb", True):
                try:
                    vector_indexer = VectorDBIndexer()
                    self.graph_builder.add_indexer(vector_indexer.name, vector_indexer)
                    logger.info("VectorDBIndexer added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize VectorDBIndexer: %s", str(e))
                    logger.debug(traceback.format_exc())
                    
            # LightRAG indexer
            if self.config.get("enable_lightrag", False):
                try:
                    lightrag_indexer = LightRAGIndexer()
                    self.graph_builder.add_indexer(lightrag_indexer.name, lightrag_indexer)
                    logger.info("LightRAGIndexer added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize LightRAGIndexer: %s", str(e))
                    logger.debug(traceback.format_exc())

        except Exception as e:
            logger.error("Error in setting up indexers: %s", str(e))
            logger.debug(traceback.format_exc())

    async def _setup_postgres_checkpointer(self):
        """Setup PostgreSQL checkpointer for persistent memory"""
        try:
            # Get PostgreSQL configuration
            self._conn_string = get_required_env("DATABASE_URL")
            
            self.checkpointer = await self.exit_stack.enter_async_context(
                AsyncPostgresSaver.from_conn_string(self._conn_string)
            )
            
            # Setup database tables (creates them if they don't exist)
            await self.checkpointer.setup()
            
            logger.info("PostgreSQL checkpointer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL checkpointer: {e}")
            # Fall back to no persistence
            self.checkpointer = None
            self._conn_string = None
            logger.warning("Continuing without persistent memory")

    def _build_graph(self):
        """Build and compile the agent's graph."""
        try:
            logger.info("Building the agent's graph...")

            memory_saver = self.config.get("memory_saver", MemorySaver())
            run_name = self.config.get("run_name", "Archivist")

            self.graph = self.graph_builder.compile(
                memory_saver=memory_saver,
                run_name=run_name
            )

            logger.info("Graph compiled successfully.")

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())

    def index(self, 
            filePath: str, 
            config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Index a document from the given file path.
        
        Args:
            filePath: Path to the file to be indexed
            config: Optional indexing configuration parameters
            
        Returns:
            Results of the indexing operation
        """
        try:
            logger.info(f"Indexing document: {filePath}")

            # Prepare input state for the indexing graph
            input_state = {
                "filePath": filePath,
                "config": config or {}
            }
            
            # Use a consistent thread ID for potential continuations
            # thread = {"configurable": {"thread_id": "indexing_" + str(hash(filePath))}}
            thread = {"configurable": {"thread_id": f"indexing_{int(time.time() * 1000)}"}}

            # Process through the graph
            result = self.graph.invoke(input_state, thread)

            logger.info(f"Document indexed successfully: {filePath}")
            
            # Return indexing results (should contain doc_id, status, etc.)
            return result

        except Exception as e:
            logger.error(f"Error indexing document {filePath}: {str(e)}")
            logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "filePath": filePath
            }

    def _build_agent(self, config: Optional[dict] = None):
        """Builds a LangGraph ReAct agent with optional model config and tools"""

        return create_react_agent(
            model=get_llm(config),
            tools=self.tools,  # Pass the tools to the agent
            prompt=ARCHIVIST_SYSTEM_PROMPT,
            checkpointer=self.checkpointer,  # Add checkpointer for persistence
        )
    
    async def process_query(self, query: str, thread_id: Optional[str] = None, config: Optional[Dict[str, Any]] = {}) -> Dict[str, Any]:
        """Process a query using the agent with persistent memory
        
        Args:
            query: The user's query
            thread_id: Optional thread ID for conversation continuity. If None, generates a new one.
            config: Optional configuration dict that can contain:
                - model: The model's configuration to use
                - model.API: The API to use for the model (e.g., openai, bedrock, google)
                - model.model_id: The specific model ID to use
            
        Returns:
            Dictionary containing the response and thread_id
        """
        logger.info(f"Processing query: {query}")
        
        # Generate thread_id if not provided
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            logger.info(f"Generated new thread_id: {thread_id}")
        else:
            logger.info(f"Using existing thread_id: {thread_id}")
        
        # Create config with thread_id for persistence
        lang_config = {"configurable": {"thread_id": thread_id}}
        agent = self._build_agent(config.get("model", {}))
        
        try:
            # Process the query with the agent
            response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config=lang_config
            )
            
            return {
                "response": response,
                "thread_id": thread_id
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }
        
    async def process_query_stream(self, query: str, thread_id: Optional[str] = None, config: Optional[Dict[str, Any]] = {}) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query using the agent with persistent memory and streaming
        
        Args:
            query: The user's query
            thread_id: Optional thread ID for conversation continuity. If None, generates a new one.
            config: Optional configuration dict that can contain:
                - model: The model's configuration to use
                - model.API: The API to use for the model (e.g., openai, bedrock, google)
                - model.model_id: The specific model ID to use
            
        Yields:
            Dictionary containing streaming chunks and thread_id
        """
        logger.info(f"Processing streaming query: {query}")
        
        # Generate thread_id if not provided
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            logger.info(f"Generated new thread_id: {thread_id}")
        else:
            logger.info(f"Using existing thread_id: {thread_id}")
        
        # Create config with thread_id for persistence
        lang_config = {"configurable": {"thread_id": thread_id}}
        
        # Create inputs
        inputs = {"messages": [{"role": "user", "content": query}]}
        agent = self._build_agent(config.get("model", {}))

        try:
            # Stream the response from the agent
            async for chunk in agent.astream(inputs, config=lang_config, stream_mode="values"):
                logger.info(f"Streaming chunk: {chunk}")
                yield {
                    "chunk": chunk,
                    "thread_id": thread_id
                }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.debug(traceback.format_exc())
            yield {
                "status": "error",
                "error": str(e),
                "query": query,
                "thread_id": thread_id
            }
    
    async def get_conversation_content(self, thread_id: str) -> List[Dict[str, Any]]:
        """Reconstruct conversation from checkpoint - groups AI/tool messages into timeline.
        
        Args:
            thread_id: The thread ID of the conversation to retrieve
            
        Returns:
            List of conversation messages in timeline format
        """
        if not self.checkpointer:
            raise RuntimeError("Persistent memory is not configured.")
        if not thread_id or thread_id.startswith("local_"):
            raise ValueError(f"Invalid thread_id: {thread_id}")

        state = await self.checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
        messages = state.checkpoint.get("channel_values", {}).get("messages") if state else None
        if not messages:
            return []

        def extract_tool_calls(msg) -> list:
            """Extract tool calls in frontend-compatible format."""
            tc = getattr(msg, "tool_calls", None)
            if not tc:
                return []

            result = []
            for t in tc:
                result.append({
                    "name": t.get("name", ""),
                    "args": t.get("args", {}),
                    "id": t.get("id", "")
                })
            return result

        def finalize_assistant_message(assistant_msg: Dict[str, Any]) -> Dict[str, Any]:
            """Finalize assistant message: extract final AI response from timeline."""
            items = assistant_msg["timelineItems"]
            ai_idxs = [i for i, it in enumerate(items) if it.get("messageType") == "ai"]

            # Use last AI message as final content
            if ai_idxs:
                assistant_msg["content"] = items[ai_idxs[-1]].get("content", "")
            else:
                assistant_msg["content"] = ""

            return assistant_msg

        conversation: List[Dict[str, Any]] = []
        current_assistant: Optional[Dict[str, Any]] = None

        # Group messages: human → user, ai+tool → assistant with timeline
        for msg in messages:
            if not hasattr(msg, "type"):
                continue

            mtype = getattr(msg, "type", "")
            content = getattr(msg, "content", "") or ""

            if mtype in ("human", "user"):
                # Finalize previous assistant message if exists
                if current_assistant:
                    conversation.append(finalize_assistant_message(current_assistant))
                    current_assistant = None
                
                conversation.append({
                    "role": "user",
                    "content": content
                })

            elif mtype == "ai":
                # Start or continue assistant message
                if not current_assistant:
                    current_assistant = {
                        "role": "assistant",
                        "content": "",
                        "timelineItems": []
                    }
                
                current_assistant["timelineItems"].append({
                    "messageType": "ai",
                    "content": content,
                    "toolCalls": extract_tool_calls(msg)
                })

            elif mtype == "tool":
                # Add tool response to current assistant timeline
                if current_assistant:
                    current_assistant["timelineItems"].append({
                        "messageType": "tool",
                        "content": content,
                        "toolCallId": getattr(msg, "tool_call_id", ""),
                        "name": getattr(msg, "name", "")
                    })

        # Finalize last assistant message if exists
        if current_assistant:
            conversation.append(finalize_assistant_message(current_assistant))

        return conversation
    