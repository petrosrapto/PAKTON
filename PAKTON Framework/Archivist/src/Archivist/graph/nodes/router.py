"""
Description:
Routing logic for determining which indexing method to use. Currently routes
all requests to the vectordb indexing method.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import Dict, Any

from Archivist.types import IndexState


def route_indexing(state: IndexState) -> str:
    """Router to determine which retrieval method to use.
    
    Args:
        state: Current state of the agent
        
    Returns:
        Name of the index method to use
    """
    
    return "vectordb"