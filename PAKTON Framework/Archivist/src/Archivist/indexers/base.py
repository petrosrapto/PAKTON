"""
Description:
Base indexer abstract class. Defines the interface that all indexer implementations
must follow for indexing documents into various data stores.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

from Archivist.types import IndexState

class BaseIndexer(ABC):
    """Base class for all indexing methods.
    
    All indexer implementations should extend this class.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this indexer."""
        pass
    
    @abstractmethod
    def index(self, docs: List[Document], **kwargs) -> None:
        """Index documents into the data store.
        
        Args:
            docs: A list of LangChain Document objects to be indexed
            **kwargs: Additional parameters specific to this indexer
        """
        pass

    def __call__(self, state: IndexState, **kwargs) -> IndexState:
        """Make the indexer callable, similar to how BaseRetriever is callable.
        
        Args:
            docs: Documents to index
            **kwargs: Additional parameters for the indexing
        """
        self.index(state['splitDocs'], **kwargs)
        return state