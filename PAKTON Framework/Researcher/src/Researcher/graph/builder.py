"""
Description:
Graph builder that constructs the StateGraph workflow for the Researcher agent.
Manages the addition of retrievers as tools and builds the execution graph with 
nodes for query extraction, retrieval routing, reranking, and response generation.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import traceback
from typing import Dict, Any, Optional, Callable

from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver

from IPython.display import Image, display

from Researcher.types import RetrievalState
from .nodes import extract_query, generate_response, tools_condition, ToolNode, rerank

from Researcher.utils import logger, config 

class GraphBuilder:
    """Builder for the Researcher agent's StateGraph."""
    
    def __init__(self):
        """Initialize the graph builder."""
        try:
            logger.info("Initializing GraphBuilder...")

            self.graph = StateGraph(RetrievalState)
            self.retrievers = {}
            self.tools = []
            logger.info("GraphBuilder initialized successfully.")

        except Exception as e:
            logger.error("Error initializing GraphBuilder: %s", str(e))
            logger.debug(traceback.format_exc())

    def add_retriever(self, name: str, retriever_func: Callable):
        """Add a retriever to the graph.
        
        Args:
            name: Name of the retriever
            retriever_func: Function that implements the retriever
        """
        try:
            logger.info(f"Adding retriever: {name}")
            self.retrievers[name] = retriever_func
            self.tools.append(retriever_func.tool)
            logger.info(f"Retriever {name} added successfully.")

        except Exception as e:
            logger.error("Error adding retriever %s: %s", name, str(e))
            logger.debug(traceback.format_exc())

    def build(self) -> StateGraph:
        """Build the complete graph.
        
        Returns:
            StateGraph for the Researcher agent
        """
        try:
            logger.info("Building the graph structure...")

            # Add processor nodes
            self.graph.add_node("extract_query", lambda state: extract_query(state, self.tools))
            self.graph.add_node("generate_response", generate_response)
            self.graph.add_node("rerank", rerank)

            self.graph.add_node("tools", lambda state: ToolNode(state, self.tools))
            self.graph.add_conditional_edges(
                "extract_query",
                tools_condition,
                {"tools": "tools", "generate_response": "generate_response"}
            )
            self.graph.add_edge("tools", "rerank")
            self.graph.add_edge("rerank", "generate_response")
            self.graph.add_edge(START, "extract_query")

            self.graph.add_edge("generate_response", END)

            logger.info("Graph structure built successfully.")

            return self.graph

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())
            return None

    def compile(self, memory_saver: Optional[MemorySaver] = None, run_name: str = "Researcher"):
        """Compile the graph.
        
        Args:
            memory_saver: Optional memory saver for checkpointing
            run_name: Name for the run configuration
            
        Returns:
            Compiled StateGraph
        """
        try:
            logger.info("Compiling the graph...")

            if memory_saver is None:
                memory_saver = MemorySaver()

            compiled_graph = self.build().compile(checkpointer=memory_saver).with_config(run_name=run_name)
            visualization = config.get("visualization", False)
            if visualization:
                self.visualize_graph(compiled_graph)
            logger.info("Graph compiled successfully.")

            return compiled_graph

        except Exception as e:
            logger.error("Error compiling the graph: %s", str(e))
            logger.debug(traceback.format_exc())
            return None

    def visualize_graph(self, graph):
        """Display the graph using IPython display for Jupyter Notebooks."""
        try:
            logger.info("Displaying graph visualization in Jupyter Notebook...")

            if not self.graph:
                raise ValueError("Graph has not been built or compiled.")

            display(Image(graph.get_graph().draw_mermaid_png()))

        except Exception as e:
            logger.error("Error displaying graph visualization: %s", str(e))
            logger.debug(traceback.format_exc())