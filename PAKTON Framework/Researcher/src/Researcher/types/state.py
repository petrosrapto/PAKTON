"""
Description:
State definition for the Researcher agent workflow. Defines the RetrievalState TypedDict 
that manages data flow through the graph, including query, instructions, retrieved documents,
response context, and configuration with proper merging for parallel node operations.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from typing import TypedDict, List, Dict, Any, Optional
from typing import Annotated
import operator
from langchain_core.documents import Document
from langgraph.graph import MessagesState

class RetrievalState(MessagesState):
    """State type for the Researcher agent.
    
    This defines the structure of data that flows through the agent's graph.
    Fields marked with Annotated and a combiner function will be properly
    merged when updated by parallel nodes in the graph.
    """
    
    # Query information
    query: Optional[str]
    # Instructions of the user
    instructions: Optional[str]
    
    # Documents retrieved from multiple sources
    # Will be combined when updated by parallel nodes
    retrievedDocuments: Annotated[Optional[List[Document]], operator.add]
    responseContext: List[Document] # the list of documents feeded to the response generator
    # Response information
    response: Optional[str]
    
    config: Optional[Dict[str, Any]]
    
    # Other configuration
    max_num_turns: Optional[int]