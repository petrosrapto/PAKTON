"""
Description:
Graph builder that constructs and compiles the StateGraph for the Interrogator agent, defining the workflow of question generation, answer retrieval, and report creation.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import traceback
from typing import Dict, Any, Optional, Callable

from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver

from IPython.display import Image, display

from Interrogator.types import InterrogationState
from .nodes import route_interrogation, generate_question, write_report, save_interrogation, get_answer, refine_answer

from Interrogator.utils import logger, config

class GraphBuilder:
    """Builder for the Interrogator agent's StateGraph."""
    
    def __init__(self):
        """Initialize the graph builder."""
        try:
            logger.info("Initializing GraphBuilder...")

            self.graph = StateGraph(InterrogationState)
            self.indexers = {}

            logger.info("GraphBuilder initialized successfully.")

        except Exception as e:
            logger.error("Error initializing GraphBuilder: %s", str(e))
            logger.debug(traceback.format_exc())

    def build(self) -> StateGraph:
        """Build the complete graph.
        
        Returns:
            StateGraph for the Interrogator agent
        """
        try:
            logger.info("Building the graph structure...")

            # Add processor nodes
            self.graph.add_node("generate_question", generate_question)
            self.graph.add_node("write_report", write_report)
            self.graph.add_node("save_interrogation", save_interrogation)
            self.graph.add_node("get_answer", get_answer)
            self.graph.add_node("refine_answer", refine_answer)

            # Define the flow
            self.graph.add_edge(START, "generate_question")
            self.graph.add_edge("save_interrogation", "write_report")
            self.graph.add_edge("write_report", END)

            # insert conversation loop
            self.graph.add_conditional_edges("generate_question", route_interrogation, ['get_answer', 'save_interrogation'])
            self.graph.add_edge("get_answer", "refine_answer")
            self.graph.add_edge("refine_answer", "generate_question")

            logger.info("Graph structure built successfully.")

            return self.graph

        except Exception as e:
            logger.error("Error building the graph: %s", str(e))
            logger.debug(traceback.format_exc())
            return None

    def compile(self, memory_saver: Optional[MemorySaver] = None, run_name: str = "Interrogator"):
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