"""
Description:
Abstract base class for all retrieval implementations in the Researcher agent.
Defines the common interface and structure that all concrete retrievers must implement,
including name, tool properties, and retrieval methods.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.base import Runnable

from Researcher.types import RetrievalState

class BaseRetriever(Runnable, ABC):
    """Base class for all retrieval methods.
    
    All retriever implementations should extend this class.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this retriever."""
        pass

    @property
    @abstractmethod
    def tool(self) -> str:
        """Return the retriever as a tool."""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve information as LangChain Document objects.
        
        Args:
            query: The search query
            **kwargs: Additional parameters specific to this retriever
            
        Returns:
            List of LangChain Document objects
        """
        pass

    def get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """
        This function makes the retriever compatible with LangChain's Retriever interface.

        Args:
            query (str): The search query.
            **kwargs: Additional parameters specific to this retriever.

        Returns:
            List[Document]: Retrieved documents.
        """
        return self.retrieve(query, **kwargs)

    def invoke(self, input: str, config: Optional[RunnableConfig] = None, **kwargs) -> List[Document]:
        """
        Implementation of the Runnable interface for compatibility with LangChain.
        
        Args:
            input: The query string
            config: Optional configuration for the runnable
            **kwargs: Additional parameters specific to this retriever
            
        Returns:
            List of retrieved documents
        """
        return self.retrieve(input, **kwargs)
    
    def __call__(self, state: RetrievalState) -> Dict[str, Any]:
        """Make the retriever callable within the LangChain graph.
        
        Args:
            state: Current state of the agent
            
        Returns:
            Updated state with retrieval results
        """
        query = state["query"]
        config = state.get("config", {})
        
        # Retrieve documents as LangChain Document objects
        documents = self.retrieve(query, **config.get(self.name, {}))
        
        # Update state with just the documents (for parallel processing)
        return {
            "retrievedDocuments": documents
        }