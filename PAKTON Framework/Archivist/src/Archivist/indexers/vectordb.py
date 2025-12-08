"""
Description:
Vector database indexer implementation. Supports both Pinecone and ChromaDB as vector stores
for storing and retrieving document embeddings with OpenAI embedding models.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
import traceback
from typing import List
from langchain_core.documents import Document

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings

from .base import BaseIndexer  # Update path if needed
from Archivist.utils import config, logger  

class VectorDBIndexer(BaseIndexer):
    """
    Indexer that supports both Pinecone and ChromaDB as vector stores for storing and retrieving document embeddings.

    This class allows dynamic selection of the vector store (Pinecone or ChromaDB) based on configuration settings.

    Attributes:
        vectordb_config (dict): Configuration settings for the vector database.
        vector_store_type (str): Selected vector store type ("pinecone" or "chroma").
        embeddings (OpenAIEmbeddings): Embedding model used for document indexing.
    """

    def __init__(self):
        """Initialize the selected vector database (Pinecone or ChromaDB) using parameters from config.yaml or environment variables."""
        try:
            self.vectordb_config = config.get("indexers.vectordb", {})
            self.vector_store_type = self.vectordb_config.get("use_vector_store", "").lower() 
            
            if not self.vector_store_type:
                raise ValueError("vector_store is required but not set in environment or config.")
            
            # Initialize embedding model
            embedding_model = self.vectordb_config.get("embedding_model", "text-embedding-3-large")
            embeddings_api_key = os.environ.get("EMBEDDINGS_API_KEY")
            if not embeddings_api_key:
                raise ValueError("EMBEDDINGS_API_KEY is required but not set in environment or config.")
            self.embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=embeddings_api_key)

            logger.info("Initializing VectorDBIndexer with vector store: %s", self.vector_store_type)

            if self.vector_store_type == "pinecone":
                self._init_pinecone()
            elif self.vector_store_type == "chroma":
                self._init_chroma_db()
            else:
                raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")

            logger.info("VectorDBIndexer initialized successfully.")

        except Exception as e:
            logger.error("Error initializing VectorDBIndexer: %s", str(e))
            logger.debug(traceback.format_exc())

    def _init_pinecone(self):
        """Initialize Pinecone vector database using API credentials and index settings."""
        from langchain_pinecone import PineconeVectorStore
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.index_name = self.vectordb_config.get("pinecone", {}).get("INDEX_NAME")
        self.host = self.vectordb_config.get("pinecone", {}).get("API_HOST")

        if not self.api_key or not self.index_name or not self.host:
            raise ValueError("Missing Pinecone credentials (PINECONE_API_KEY, INDEX_NAME, API_HOST).")

        # Initialize Pinecone
        pc = Pinecone(api_key=self.api_key, base_url=self.host)
        self.pc_index = pc.Index(self.index_name)

        logger.info("Pinecone initialized with index: %s", self.index_name)

    def _init_chroma_db(self):
        """Initialize ChromaDB vector database using settings from config.yaml."""
        from langchain_chroma import Chroma
        from chromadb.config import Settings

        # Load Chroma configuration
        chroma_config = self.vectordb_config.get("chroma", {})

        self.index_name = chroma_config.get("INDEX_NAME")
        persist_directory = chroma_config.get("persist_directory", "./chroma_db")  # Default directory
        collection_metadata = chroma_config.get("metadata", {})

        if not self.index_name:
            raise ValueError("Missing Chroma index name in config.yaml.")

        client_settings = Settings(persist_directory=persist_directory, anonymized_telemetry=False)

        self.db = Chroma(
            collection_name=self.index_name,
            embedding_function=self.embeddings,
            client_settings=client_settings,
            collection_metadata=collection_metadata
        )

        logger.info("ChromaDB initialized with index: %s, persist_directory: %s", self.index_name, persist_directory)

    @property
    def name(self) -> str:
        """Return the unique name of this indexer."""
        return "vectordb"
    
    def index(self, docs: List[Document], **kwargs) -> None:
        """
        Index (upsert) documents into the selected vector store (Pinecone or ChromaDB).

        Args:
            docs (List[Document]): A list of LangChain Document objects to be indexed.
            **kwargs: Additional parameters, e.g., chunk_size.
        """
        try:
            logger.info("Indexing %d documents into %s...", len(docs), self.vector_store_type)

            # Delete all existing documents before indexing (For testing purposes)
            self.delete_all()

            if self.vector_store_type == "pinecone":
                # Convert docs to a PineconeVectorStore and upsert them
                vectorstore = PineconeVectorStore.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    index_name=self.index_name,
                )
            elif self.vector_store_type == "chroma":
                self.db.add_documents(docs)

            logger.info("Successfully indexed documents into %s (Index Name: %s)", self.vector_store_type, self.index_name)

        except Exception as e:
            logger.error("Error indexing documents to %s: %s", self.vector_store_type, str(e))
            logger.debug(traceback.format_exc())

    def delete_all(self) -> None:
        """
        Deletes all documents stored in the selected vector database.

        - If Pinecone is used, it removes all vectors from the index.
        - If ChromaDB is used, it removes all stored documents.

        Logs:
            - Logs when deletion starts and completes.
            - Logs any errors that occur during deletion.
        """
        try:
            logger.info("Deleting all documents from %s index: %s", self.vector_store_type, self.index_name)

            if self.vector_store_type == "pinecone":
                # Delete all vectors from the Pinecone index
                self.pc_index.delete(delete_all=True)
            elif self.vector_store_type == "chroma":
                # Delete all documents from ChromaDB
                ids = self.db._collection.get()["ids"]
                if ids:  # Check if there are any documents to delete
                    self.db._collection.delete(ids)

            logger.info("Successfully deleted all documents from %s index: %s", self.vector_store_type, self.index_name)

        except Exception as e:
            logger.error("Error deleting documents from %s: %s", self.vector_store_type, str(e))
            logger.debug(traceback.format_exc())