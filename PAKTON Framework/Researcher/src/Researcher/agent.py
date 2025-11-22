"""
Description:
Main Researcher agent implementation that orchestrates multiple retrieval sources 
(web search, Wikipedia, vector databases, BM25, hybrid, and LightRAG) using a StateGraph 
architecture for intelligent information retrieval and synthesis.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import traceback
from typing import Dict, Any, List, Optional

from langgraph.checkpoint.memory import MemorySaver

import time

from Researcher.graph import GraphBuilder
from Researcher.retrievers import WikipediaRetriever, WebRetriever, VectorDBRetriever, BM25RetrieverWrapper, HybridRetriever, LightRAGRetriever

from Researcher.utils import logger  # Import the logger

class Researcher:
    """Researcher agent for retrieving and processing information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Researcher agent.
        
        Args:
            config: Configuration for the agent
        """
        try:
            self.config = config or {}
            self.graph_builder = GraphBuilder()
            self.graph = None
            
            logger.info("Initializing Researcher with config: %s", self.config)

            # Set up retrievers
            self._setup_retrievers()

            # Build and compile the graph
            self._build_graph()

        except Exception as e:
            logger.error("Error initializing Researcher: %s", str(e))
            logger.debug(traceback.format_exc())
    
    def _setup_retrievers(self):
        """Set up the retriever components."""
        try:
            logger.info("Setting up retrievers...")

            # Web search retriever
            if self.config.get("enable_web", False):
                try:
                    web_retriever = WebRetriever()
                    self.graph_builder.add_retriever(web_retriever.name, web_retriever)
                    logger.info("WebRetriever added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize WebRetriever: %s", str(e))
                    logger.debug(traceback.format_exc())
            # Wikipedia retriever
            if self.config.get("enable_wikipedia", False):
                try:
                    wiki_retriever = WikipediaRetriever()
                    self.graph_builder.add_retriever(wiki_retriever.name, wiki_retriever)
                    logger.info("WikipediaRetriever added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize WikipediaRetriever: %s", str(e))
                    logger.debug(traceback.format_exc())

            # Vector DB retriever
            if self.config.get("enable_vectordb", False):
                try:
                    vector_retriever = VectorDBRetriever()
                    self.graph_builder.add_retriever(vector_retriever.name, vector_retriever)
                    logger.info("VectorDBRetriever added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize VectorDBRetriever: %s", str(e))
                    logger.debug(traceback.format_exc())

            if self.config.get("enable_bm25", False):
                try:
                    bm25_retriever = BM25RetrieverWrapper()
                    self.graph_builder.add_retriever(bm25_retriever.name, bm25_retriever)
                    logger.info("BM25RetrieverWrapper added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize BM25RetrieverWrapper: %s", str(e))
                    logger.debug(traceback.format_exc())
            
            if self.config.get("enable_hybrid", False):
                try:
                    hybrid_retriever = HybridRetriever()
                    self.graph_builder.add_retriever(hybrid_retriever.name, hybrid_retriever)
                    logger.info("HybridRetriever added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize HybridRetriever: %s", str(e))
                    logger.debug(traceback.format_exc())
                    
            # LightRAG retriever
            if self.config.get("enable_lightrag", False):
                try:
                    lightrag_retriever = LightRAGRetriever()
                    self.graph_builder.add_retriever(lightrag_retriever.name, lightrag_retriever)
                    logger.info("LightRAGRetriever added successfully.")
                except Exception as e:
                    logger.error("Failed to initialize LightRAGRetriever: %s", str(e))
                    logger.debug(traceback.format_exc())

        except Exception as e:
            logger.error("Error in setting up retrievers: %s", str(e))
            logger.debug(traceback.format_exc())

    def _build_graph(self):
        """Build and compile the agent's graph."""
        try:
            logger.info("Building the agent's graph...")

            memory_saver = self.config.get("memory_saver", MemorySaver())
            run_name = self.config.get("run_name", "Researcher")

            self.graph = self.graph_builder.compile(
                memory_saver=memory_saver,
                run_name=run_name
            )

            logger.info("Graph compiled successfully.")

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())

    def search(self, 
               query: str, 
               instructions: Optional[str] = "",
               max_num_turns: int = 1,
               config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a search query through the agent.
        
        Args:
            query: The search query
            instructions: Optional instructions to guide the search
            max_num_turns: Maximum number of interaction turns
            config: Optional run-specific configuration
            
        Returns:
            Results of the search
        """
        try:
            logger.info("Running search query: %s", query)

            input_state = {
                "query": query,
                "instructions": instructions,
                "max_num_turns": max_num_turns,
                "config": config or {}
            }
            # thread = {"configurable": {"thread_id": "indexing_" + str(hash(str(query)))}}  
            thread = {"configurable": {"thread_id": f"indexing_{int(time.time() * 1000)}"}}

            result = self.graph.invoke(input_state, thread)

            logger.info("Search completed successfully.")

            return result

        except Exception as e:
            logger.error("Error executing search: %s", str(e))
            logger.debug(traceback.format_exc())
            return {}