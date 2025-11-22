"""
Description:
Main Interrogator agent implementation that conducts iterative interviews with the RAG agent to extract comprehensive legal information through strategic questioning.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import traceback
from typing import Dict, Any, List, Optional

from langgraph.checkpoint.memory import MemorySaver

import time

from Interrogator.graph import GraphBuilder

from Interrogator.utils import config as globalConfig, logger  

class Interrogator:
    """Interrogator agent for conducting interviews to the RAG agent."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the interrogator agent.
        
        Args:
            config: Configuration for the agent
        """
        try:
            self.config = config or {}
            self.graph_builder = GraphBuilder()
            self.graph = None
            
            logger.info("Initializing Interrogator with config: %s", self.config)

            # Build and compile the graph
            self._build_graph()

        except Exception as e:
            logger.error("Error initializing Interrogator: %s", str(e))
            logger.debug(traceback.format_exc())

    def _build_graph(self):
        """Build and compile the agent's graph."""
        try:
            logger.info("Building the agent's graph...")

            memory_saver = self.config.get("memory_saver", MemorySaver())
            run_name = self.config.get("run_name", "Interrogator")

            self.graph = self.graph_builder.compile(
                memory_saver=memory_saver,
                run_name=run_name
            )

            logger.info("Graph compiled successfully.")

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())

    def interrogation(self, 
                    userQuery: str, 
                    userContext: Optional[str] = None,
                    userInstructions: Optional[str] = None,
                    config: Optional[Dict[str, Any]] = {}) -> Dict[str, Any]:
        """
        Executes the interrogation workflow for a given user query through the agent's graph.
        
        This method processes a user's query through the Interrogator's computational graph,
        which analyzes the query, generates appropriate follow-up questions, and produces
        a structured response. The graph maintains conversation state across invocations
        using a thread ID derived from the query hash.
        
        Args:
            userQuery: The user's natural language query or question to be analyzed
            config: Optional configuration overrides for this specific interrogation,
                    can include parameters like:
                    - max_questions: Maximum number of follow-up questions to generate
                    - depth_first: Whether to use depth-first vs breadth-first questioning
                    - domain_context: Additional context about the domain of inquiry
                    - mode: Interrogation mode (e.g., "exploratory", "critical", "validating")
        
        Returns:
            A dictionary containing the interrogation results with keys such as:
            - status: "success" or "error"
            - response: The final comprehensive answer
            - questions: List of follow-up questions that were generated
            - reasoning: The agent's reasoning process
            - confidence: Confidence scores for different parts of the response
            - errors: Any non-fatal errors encountered during processing
        
        Raises:
            No exceptions are raised directly as they are caught and returned as error responses
        
        Example:
            ```python
            interrogator = Interrogator(config)
            result = interrogator.interrogation("How does transformer architecture work?")
            print(result["response"])
            ```
            
        Note:
            The method maintains thread continuity, allowing for conversation history
            to be preserved across multiple calls with related queries.
        """
        try:
            logger.info(f"Starting interrogation for user query: {userQuery}")

            max_num_turns = config.get("max_num_turns", globalConfig.get("interrogation", {}).get("max_num_turns", 1))

            input_state = {
                "userQuery": userQuery,
                "userContext": userContext,
                "userInstructions": userInstructions,
                "max_num_turns": max_num_turns,
                "config": config or {}
            }
            
            # Use a consistent thread ID for potential continuations
            # thread = {"configurable": {"thread_id": "indexing_" + str(hash(userQuery))}}
            thread = {"configurable": {"thread_id": f"indexing_{int(time.time() * 1000)}"}}

            result = self.graph.invoke(input_state, thread)

            logger.info(f"Interrogation successful for userQuery: {userQuery}")

            return result

        except Exception as e:
            logger.error(f"Error in interrogation for {userQuery}: {str(e)}")
            logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "userQuery": userQuery
            }