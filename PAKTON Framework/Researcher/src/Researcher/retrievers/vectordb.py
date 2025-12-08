"""
Description:
Vector database retriever implementation supporting both Pinecone and ChromaDB for
semantic search. Encodes text as numerical vectors and retrieves closest matching
documents using vector similarity rather than keyword matching.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
import traceback
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader

from langchain_openai import OpenAIEmbeddings

from langchain.tools import Tool

class VectorDBRetriever(BaseRetriever):
    """
    A retriever that supports **both Pinecone and ChromaDB** for vector-based semantic search.

    Instead of keyword matching, this retriever **encodes text as numerical vectors** 
    and retrieves the closest matching documents in the vector space.

    Features:
    - Stores document embeddings in either **Pinecone or ChromaDB**.
    - Retrieves documents using **vector similarity search**.
    - Supports **dynamic selection of vector store** via config.
    - Provides a method to fetch all stored documents for hybrid search.

    Attributes:
        vectordb_config (dict): Configuration settings for the vector database.
        vector_store_type (str): Selected vector store type ("pinecone" or "chroma").
        retriever: The vector database retriever (Pinecone or ChromaDB).
    """

    def __init__(self):
        """
        Initializes the **Pinecone or ChromaDB retriever** using parameters from `config.yaml`.

        Raises:
            ValueError: If required credentials are missing.
            Exception: If an error occurs during initialization.
        """
        try:
            # Load vector database configuration
            self.vectordb_config = config.get("retrievers.vectordb", {})
            self.vector_store_type = self.vectordb_config.get("use_vector_store", "").lower()

            if not self.vector_store_type:
                raise ValueError("vector_store is required but not set in environment or config.")

            logger.info("Initializing VectorDBRetriever with vector store: %s", self.vector_store_type)

            # Initialize OpenAI embeddings model
            embedding_model = self.vectordb_config.get("embedding_model", "text-embedding-3-large")

            embeddings_api_key = os.environ.get("EMBEDDINGS_API_KEY")
            if not embeddings_api_key:
                raise ValueError("EMBEDDINGS_API_KEY is required but not set in environment or config.")

            self.embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=embeddings_api_key)

            self.top_k = self.vectordb_config.get("top_k", 5)
            self.similarity_threshold = self.vectordb_config.get("similarity_threshold", 0)

            # Initialize the selected vector store
            if self.vector_store_type == "pinecone":
                self._init_pinecone()
            elif self.vector_store_type == "chroma":
                self._init_chroma_db()
            else:
                raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")
            
            # self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.top_k})

            logger.info("Initializing VectorDBRetriever with config: %s", self.vectordb_config)

        except Exception as e:
            logger.error("Error initializing VectorDBRetriever: %s", str(e))
            logger.debug(traceback.format_exc())

    def _init_pinecone(self):
        """Initialize Pinecone retriever using API credentials and index settings."""
        from langchain_pinecone import PineconeVectorStore
        
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.index_name = self.vectordb_config.get("pinecone", {}).get("INDEX_NAME")
        self.host = self.vectordb_config.get("pinecone", {}).get("API_HOST")

        if not self.api_key or not self.index_name or not self.host:
            raise ValueError("Missing Pinecone credentials (PINECONE_API_KEY, INDEX_NAME, API_HOST).")

        # Initialize Pinecone vector store
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )

        logger.info("Pinecone retriever initialized with index: %s", self.index_name)

    def _init_chroma_db(self):
        """Initialize ChromaDB retriever using settings from config.yaml."""
        from langchain_chroma import Chroma
        from chromadb.config import Settings

        chroma_config = self.vectordb_config.get("chroma", {})

        self.index_name = chroma_config.get("INDEX_NAME")
        persist_directory = chroma_config.get("persist_directory", "/chroma_db")  # Default to /chroma_db
        collection_metadata = chroma_config.get("metadata", {})

        if not self.index_name or not persist_directory:
            raise ValueError("Missing Chroma index name or persist directory in config.yaml.")

        client_settings = Settings(persist_directory=persist_directory, anonymized_telemetry=False)

        self.vectorstore = Chroma(
            collection_name=self.index_name,
            embedding_function=self.embeddings,
            client_settings=client_settings,
            collection_metadata=collection_metadata
        )
        
        logger.info("ChromaDB retriever initialized with index: %s, persist_directory: %s", self.index_name, persist_directory)

    @property
    def name(self) -> str:
        """Returns the unique name of this retriever."""
        return "vectordb_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves documents from the selected vector database (Pinecone or ChromaDB) 
        based on **semantic similarity**.

        This method encodes the query as a vector and performs a **nearest neighbor search**
        in the vector database to retrieve the most relevant documents.

        Args:
            query (str): The input search query.
            **kwargs: Additional parameters, such as `k` to specify the number of top results.

        Returns:
            List[Document]: A ranked list of retrieved documents.

        Logs:
            - Logs the query execution process.
            - Logs the number of documents retrieved.
        """
        try:
            logger.info("Retrieving vector DB documents for query: %s", query)

            # Override top_k if provided
            top_k = kwargs.get("k", self.top_k)
            similarity_threshold = kwargs.get("similarity_threshold", self.similarity_threshold)
                
            # Retrieve relevant documents
            retrieved_results = self.vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
            documents = []
            for doc, score in retrieved_results:
                if score <= similarity_threshold:
                    continue
                doc.metadata["retriever"] = self.name
                doc.metadata["vectordb_similarity_score"] = score  # Add similarity score to metadata
                documents.append(doc)

            logger.info("Successfully retrieved %d documents from %s", len(documents), self.vector_store_type)
            return documents

        except Exception as e:
            logger.error("Error retrieving from %s: %s", self.vector_store_type, str(e))
            logger.debug(traceback.format_exc())
            return []

    def fetch_all_documents(self) -> List[Document]:
        """
        Fetches **all stored documents** from the selected vector database (Pinecone or ChromaDB).

        This is useful for:
        - **Hybrid search** (combining BM25 & vector search).
        - **Retrieval debugging** (checking what documents are indexed).
        - **Refreshing document metadata**.

        Returns:
            List[Document]: A list of all stored documents.

        Logs:
            - Logs the number of documents retrieved.
        """
        try:
            logger.info("Fetching all documents from %s index: %s", self.vector_store_type, self.index_name)

            if self.vector_store_type == "pinecone":
                all_docs = self.invoke(" ", k=10000)
            elif self.vector_store_type == "chroma":
                all_docs = self.vectorstore.get()
                documents = all_docs["documents"]  # List of document texts
                metadata = all_docs["metadatas"]   # List of metadata dictionaries
                all_docs = []
                
                # Filter out None or empty document texts
                for text, meta in zip(documents, metadata):
                    if text is not None:  # Skip documents with None content
                        all_docs.append(Document(page_content=text, metadata=meta or {}))
                    else:
                        logger.warning("Skipping document with None content")
            else:
                raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

            logger.info("Fetched %d documents from %s", len(all_docs), self.vector_store_type)
            return all_docs

        except Exception as e:
            logger.error("Error fetching documents from %s: %s", self.vector_store_type, str(e))
            logger.debug(traceback.format_exc())
            return []
        
    @property
    def tool(self) -> Tool:
        return Tool(
            name="DocumentSearch",
            func=lambda query: self.retrieve(query),
            description="Searches the document database for stored documents. Use this when search for documents is needed, especially when a specific name of a document is given.",
        )