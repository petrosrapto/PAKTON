"""
Description:
State definition for the Archivist agent. Defines the IndexState TypedDict that maintains
file paths, split documents, and configuration throughout the indexing workflow.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import TypedDict, List, Dict, Any, Optional
from typing import Annotated
import operator
from langchain_core.documents import Document

class IndexState(TypedDict):
    """
        State type for the Archivist agent.
    """

    filePath: Optional[str]
    splitDocs: Optional[List[Document]]
    config: Optional[Dict[str, Any]]
