"""
Description:
Hybrid retrieval implementation combining multiple search strategies (semantic vector
search and lexical BM25 search) using rank fusion techniques to improve document
retrieval effectiveness through weighted aggregation and rank-based merging.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10

Technical Implementation:
Hybrid (Ensemble) Retrieval using Rank Fusion

### Theoretical Background:
Hybrid retrieval combines **multiple search strategies** (e.g., **semantic vector search** and **lexical BM25 search**) 
to improve document retrieval effectiveness. A common approach is **rank fusion**, where results from 
different retrieval models are **merged and re-ranked** to provide the most relevant documents.

### How Rank Fusion Works:
1. **Lexical Search (BM25)**:
   - Finds documents containing **exact words** from the query.
   - Useful for handling **rare or domain-specific keywords**.

2. **Semantic Search (Embeddings / Vector Search)**:
   - Finds documents based on **semantic meaning** rather than exact matches.
   - Captures **contextually similar** documents using **vector embeddings**.

3. **Fusion of Results**:
   - **Weighted Aggregation**: Assigns different weights to BM25 and Vector Search results.
   - **Rank-Based Merging**: Combines rankings from both search methods into a final ranking.
   - **Re-Ranking**: Scores are normalized and aggregated to balance **precision vs recall**.

### Why Use Hybrid Retrieval?
- **Combines strengths** of both retrieval models (lexical & semantic).
- **Improves recall** (BM25 finds rare terms, embeddings find similar meanings).
- **Reduces dependency** on exact phrasing of queries.
- **More robust retrieval** across different types of text-based data.

This module implements hybrid retrieval by **combining BM25 (Lexical) and Vector search**
using LangChain's **EnsembleRetriever**, allowing **weighted retrieval fusion**.

Author: Petros Raptopoulos (petrosrapto@gmai.com)
Date: 7.3.2025
"""

import traceback
from typing import List
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader
from .vectordb import VectorDBRetriever
from .bm25 import BM25RetrieverWrapper

from langchain.tools import Tool

class HybridRetriever(BaseRetriever):
    """
    A hybrid retriever that **combines BM25 lexical search and vector search** using 
    **rank fusion** to improve document retrieval quality.

    This retriever merges **exact keyword matches (BM25)** with **semantic similarity matches (vector search)**
    by assigning **weighted contributions** to both methods.

    Features:
    - **Ensemble Ranking**: Uses LangChain's `EnsembleRetriever` to merge results.
    - **Weighted Fusion**: Configurable weighting for BM25 and vector-based retrieval.
    - **Automatic Document Fetching**: Loads documents from vector database for BM25 processing.

    Attributes:
        hybrid_config (dict): Configuration settings for ensemble retrieval.
        embeddings_retriever (VectorDBRetriever): Semantic search retriever.
        bm25_retriever (BM25RetrieverWrapper): Lexical search retriever using BM25.
        retriever (EnsembleRetriever): LangChain ensemble retriever for hybrid ranking.
    """

    def __init__(self):
        """
        Initializes the **hybrid retriever**, combining **BM25 lexical search** and **vector search**.

        - **BM25 Retriever**: Uses indexed textual chunks for fast keyword-based lookup.
        - **Vector Retriever**: Uses embeddings to find semantically related documents.
        - **Rank Fusion**: Combines and re-ranks results using configurable weights.

        Raises:
            Exception: If retrieval initialization fails.
        """
        try:
            # Load hybrid retriever settings
            self.hybrid_config = config.get("retrievers.hybrid", {})

            # Initialize the VectorDBRetriever for semantic search
            self.embeddings_retriever = VectorDBRetriever()

            # Retrieve weight configurations
            self.bm25_weight = self.hybrid_config.get("bm25_weight", 0.5)
            self.vector_weight = self.hybrid_config.get("vector_weight", 0.5)

            # Log the initialization of hybrid retrieval
            logger.info(
                "Initializing HybridRetriever with BM25 weight: %.2f, Vector weight: %.2f",
                self.bm25_weight,
                self.vector_weight,
            )
        except Exception as e:
            logger.error("Error initializing HybridRetriever: %s", str(e))
            logger.debug(traceback.format_exc())

    @property
    def name(self) -> str:
        """
        Returns the unique name identifier of this retriever.

        Returns:
            str: The retriever's name identifier.
        """
        return "hybrid_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves documents using **hybrid rank fusion retrieval**.

        This method performs:
        - **BM25 Search**: Finds exact keyword-based matches.
        - **Vector Search**: Finds semantically similar documents.
        - **Rank Fusion**: Merges and re-ranks results based on weighted scores.

        Args:
            query (str): The input search query.
            **kwargs: Additional parameters, such as `k` to specify the number of top results.

        Returns:
            List[Document]: A **ranked list** of the most relevant documents.

        Logs:
            - Logs the query execution and retrieval process.
            - Logs the number of documents retrieved.
        """
        try:
            logger.info("Retrieving hybrid search results for query: %s", query)

            # Override top_k if provided
            top_k = kwargs.get("k", self.hybrid_config.get("top_k", 5))

            # Fetch all stored documents from the vector database for BM25 processing
            vectordb_documents = self.embeddings_retriever.fetch_all_documents()
            self.bm25_retriever = BM25RetrieverWrapper(vectordb_documents)

            # Create an EnsembleRetriever to merge BM25 and Vector results
            # Both retrievers now properly implement the Runnable interface
            self.retriever = EnsembleRetriever(
                retrievers=[self.bm25_retriever, self.embeddings_retriever],
                weights=[self.bm25_weight, self.vector_weight],
            )
            
            # Retrieve documents using rank fusion
            all_documents = self.retriever.invoke(query)
             # Limit to top_k results
            documents = all_documents[:top_k] if len(all_documents) > top_k else all_documents

            for doc in documents:
                doc.metadata["retriever"] = self.name

            logger.info("Successfully retrieved %d hybrid search results", len(documents))
            return documents

        except Exception as e:
            logger.error("Error retrieving from hybrid retriever: %s", str(e))
            logger.debug(traceback.format_exc())
            return []
        
    @property
    def tool(self) -> Tool:
        return Tool(
            name="DocumentSearch",
            func=lambda query: self.retrieve(query),
            description="Searches the document database for stored documents. Use this when explicitly said or a specific name of a document is given.",
        )