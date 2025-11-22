"""
Description:
Retrievers module containing all document retrieval implementations for the Researcher agent.
Provides various retrieval strategies including web search, Wikipedia, vector databases,
BM25, hybrid fusion, and LightRAG graph-based retrieval.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""

from .base import BaseRetriever
from .web import WebRetriever
from .wikipedia import WikipediaRetriever
from .vectordb import VectorDBRetriever
from .bm25 import BM25RetrieverWrapper
from .hybrid import HybridRetriever
from .lightrag import LightRAGRetriever

__all__ = [
    "BaseRetriever",
    "WebRetriever",
    "WikipediaRetriever",
    "VectorDBRetriever",
    "BM25RetrieverWrapper",
    "HybridRetriever",
    "LightRAGRetriever"
]