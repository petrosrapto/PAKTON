"""
Description:
Type definitions and data structures for the Researcher agent.
Defines state management types, query models, and other data structures
used throughout the retrieval workflow.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from .state import RetrievalState
from .search_query import SearchQuery

__all__ = ["RetrievalState", "SearchQuery"]