"""
Description:
Graph builder for the Archivist agent. Constructs and compiles the StateGraph workflow
that orchestrates document parsing and indexing operations in parallel.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import traceback
from typing import Dict, Any, Optional, Callable

from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver

from IPython.display import Image, display

from Archivist.types import IndexState
from .nodes import parse_and_split

from Archivist.utils import logger, config

class GraphBuilder:
    """Builder for the Archivist agent's StateGraph."""
    
    def __init__(self):
        """Initialize the graph builder."""
        try:
            logger.info("Initializing GraphBuilder...")

            self.graph = StateGraph(IndexState)
            self.indexers = {}

            logger.info("GraphBuilder initialized successfully.")

        except Exception as e:
            logger.error("Error initializing GraphBuilder: %s", str(e))
            logger.debug(traceback.format_exc())

    def add_indexer(self, name: str, indexer_func: Callable):
        """Add a indexer to the graph.
        
        Args:
            name: Name of the indexer
            indexer_func: Function that implements the indexer
        """
        try:
            logger.info(f"Adding indexer: {name}")

            self.graph.add_node(name, indexer_func)
            self.indexers[name] = indexer_func

            logger.info(f"Indexer {name} added successfully.")

        except Exception as e:
            logger.error("Error adding indexer %s: %s", name, str(e))
            logger.debug(traceback.format_exc())

    def build(self) -> StateGraph:
        """Build the complete graph.
        
        Returns:
            StateGraph for the Archivist agent
        """
        try:
            logger.info("Building the graph structure...")

            # Add processor nodes
            self.graph.add_node("parse_and_split", parse_and_split)

            # Define the flow
            self.graph.add_edge(START, "parse_and_split")

            # Create a parallel execution pattern - all indexers run after parsing
            if self.indexers:
                for name in self.indexers.keys():
                    # Connect parse_and_split to each indexer
                    self.graph.add_edge("parse_and_split", name)
                    # Connect each indexer to END
                    self.graph.add_edge(name, END)
            else:
                # If no indexers are configured, connect parse_and_split directly to END
                logger.warning("No indexers configured - connecting parse_and_split directly to END")
                self.graph.add_edge("parse_and_split", END)

            logger.info("Graph structure built successfully.")

            return self.graph

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())
            return None

    def compile(self, memory_saver: Optional[MemorySaver] = None, run_name: str = "Archivist"):
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