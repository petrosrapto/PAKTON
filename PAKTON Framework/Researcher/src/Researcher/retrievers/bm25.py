"""
Description:
BM25 (Best Matching 25) retriever implementation with scoring functionality.
Provides lexical search capabilities using statistical ranking functions for
relevance-based document retrieval with access to BM25 scores.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10

Technical Implementation:
BM25 Retriever Wrapper with Scores

This module implements a retriever using the BM25 (Best Matching 25) algorithm,
with added functionality to access the BM25 scores for each retrieved document.
"""

import traceback
from typing import List, Optional, Tuple, Dict, Any
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever as LangChainBM25Retriever
from rank_bm25 import BM25Okapi
import numpy as np

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader

from langchain.tools import Tool

def sigmoid(x):
    """Apply sigmoid transformation to normalize scores between 0 and 1."""
    return 1 / (1 + np.exp(-x))

class BM25RetrieverWrapper(BaseRetriever):
    """
    A wrapper for the BM25Retriever with score access capability.
    """

    def __init__(self, documents: Optional[List[Document]] = None):
        """
        Initializes the BM25Retriever with provided documents or loads them from storage if none are given.
        """
        try:
            # Load documents if none are provided
            if documents is None:
                logger.info("No documents provided. Loading documents from storage...")
                self.documents = self._load_documents()
            else:
                self.documents = documents

            # Log initialization
            logger.info("Initializing BM25Retriever with %d documents", len(self.documents))

            self.bm25_config = config.get("retrievers.bm25", {})
            self.top_k = self.bm25_config.get("top_k", 5)
            self.similarity_threshold = self.bm25_config.get("similarity_threshold", 0)
            self.use_sigmoid = self.bm25_config.get("use_sigmoid", True)
            
            # Store the LangChain retriever
            # self.retriever = LangChainBM25Retriever.from_documents(self.documents, k=self.top_k)
            
            # Also create a custom BM25 instance for direct score access
            self.doc_texts = [doc.page_content for doc in self.documents]
            self.tokenized_docs = [doc.split() for doc in self.doc_texts]
            self.bm25 = BM25Okapi(self.tokenized_docs)
            
            logger.info("BM25Retriever initialized successfully with BM25Okapi instance")

        except Exception as e:
            logger.error("Error initializing BM25Retriever: %s", str(e))
            logger.debug(traceback.format_exc())
            # Re-raise the exception to prevent creating an unusable instance
            raise

    def _load_documents(self) -> List[Document]:
        """
        Loads stored document splits from a predefined storage source.
        """
        try:
            logger.info("Fetching stored document splits...")

            from .vectordb import VectorDBRetriever
            vector_retriever = VectorDBRetriever()
            documents = vector_retriever.fetch_all_documents()
            return documents

        except Exception as e:
            logger.error("Error loading documents for BM25: %s", str(e))
            logger.debug(traceback.format_exc())
            return []

    @property
    def name(self) -> str:
        """
        Returns the unique name of this retriever.
        """
        return "bm25_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves relevant documents using BM25 lexical search.
        
        Args:
            query (str): The search query string.
            **kwargs: Additional parameters, such as `k` to specify the number of top results.

        Returns:
            List[Document]: A list of retrieved documents ranked by relevance.
        """
        try:
            logger.info("Retrieving BM25 documents for query: %s", query)
            top_k = kwargs.get("k", self.top_k)

            # Get documents with scores
            documents_with_scores = self.retrieve_with_scores(query, k=top_k)
            
            # Extract documents and add metadata with scores
            documents = []
            for doc, score in documents_with_scores:
                doc.metadata["retriever"] = self.name
                doc.metadata["bm25_score"] = score
                documents.append(doc)

            logger.info("Successfully retrieved %d documents from bm25", len(documents))
            logger.info("Documents retrieved: %s", str(documents))

            return documents
        except Exception as e:
            logger.error("Error retrieving from BM25: %s", str(e))
            logger.debug(traceback.format_exc())
            raise

    def retrieve_with_scores(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """
        Retrieves documents along with their BM25 scores.
        
        Args:
            query (str): The search query string.
            k (int, optional): Number of top documents to retrieve.
            
        Returns:
            List[Tuple[Document, float]]: List of tuples containing documents and their scores.
        """
        try:
            k = k or self.top_k
            
            # Tokenize query
            tokenized_query = query.split()
            
            # Get BM25 scores
            scores = self.bm25.get_scores(tokenized_query)
            
            # Apply sigmoid transformation if enabled
            if self.use_sigmoid:
                scores = sigmoid(scores)
                logger.info("Applied sigmoid transformation to BM25 scores")
            
            # Get top-k document indices
            top_indices = np.argsort(scores)[-k:][::-1]
            
            # Return documents with scores
            results = []
            for idx in top_indices:
                if scores[idx] > self.similarity_threshold:
                    doc = self.documents[idx]
                    results.append((doc, float(scores[idx])))
            
            return results
            
        except Exception as e:
            logger.error("Error retrieving documents with scores: %s", str(e))
            logger.debug(traceback.format_exc())
            raise

    @property
    def tool(self) -> Tool:
        return Tool(
            name="DocumentSearch",
            func=lambda query: self.retrieve(query),
            description="Searches the document database for stored documents. Use this when search for documents is needed, especially when a specific name of a document is given.",
        )