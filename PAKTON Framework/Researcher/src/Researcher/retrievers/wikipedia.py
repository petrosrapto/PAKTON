"""
Description:
Wikipedia retriever implementation for accessing Wikipedia articles and content.
Provides structured access to Wikipedia's knowledge base using LangChain's
WikipediaRetriever with configurable document limits and search parameters.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import traceback
from typing import List
from langchain_core.documents import Document
from langchain_community.retrievers import WikipediaRetriever as LangChainWikipediaRetriever

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader

from langchain.tools import Tool    

class WikipediaRetriever(BaseRetriever):
    """Retriever that searches Wikipedia for information using LangChain's WikipediaRetriever."""
    
    def __init__(self):
        """Initialize the Wikipedia retriever using parameters from config.yaml"""
        try:
            wiki_config = config.get("retrievers.wikipedia", {})

            self.load_max_docs = wiki_config.get("load_max_docs", 2)
            self.lang = wiki_config.get("lang", "en")
            self.load_all_available_meta = wiki_config.get("load_all_available_meta", True)
            self.doc_content_chars_max = wiki_config.get("doc_content_chars_max", 100000)

            # Log configuration loading
            logger.info("Initializing WikipediaRetriever with config: %s", wiki_config)

            # Initialize the LangChain WikipediaRetriever
            self.retriever = LangChainWikipediaRetriever(
                top_k_results=self.load_max_docs,
                lang=self.lang,
                load_all_available_meta=self.load_all_available_meta,
                doc_content_chars_max=self.doc_content_chars_max
            )

        except Exception as e:
            logger.error("Error initializing WikipediaRetriever: %s", str(e))
            logger.debug(traceback.format_exc())

    @property
    def name(self) -> str:
        """Return the unique name of this retriever."""
        return "wikipedia_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve information as LangChain Document objects.
        
        Args:
            query: The search query
            **kwargs: Additional parameters for the search
            
        Returns:
            List of LangChain Document objects
        """
        try:
            # Override with any provided parameters
            load_max_docs = kwargs.get("load_max_docs", self.load_max_docs)

            # Update retriever config if needed
            if load_max_docs != self.retriever.top_k_results:
                self.retriever.top_k_results = load_max_docs
                logger.info("Updated top_k_results to: %d", load_max_docs)

            logger.info("Retrieving Wikipedia documents for query: %s", query)

            # Perform search
            documents = self.retriever.invoke(query)

            for doc in documents:
                doc.metadata["retriever"] = self.name

            logger.info("Successfully retrieved %d documents", len(documents))
            logger.info("Documents retrieved: %s", str(documents))

            return documents

        except Exception as e:
            logger.error("Error retrieving from Wikipedia: %s", str(e))
            logger.debug(traceback.format_exc())
            return []
    
    @property
    def tool(self) -> Tool:
        """
        Returns the WikipediaRetriever as a LangChain Tool.

        This tool enables agents to search Wikipedia for accurate and well-sourced information 
        on a wide range of topics. Use it when:
        
        - A query requires factual knowledge from a reliable encyclopedia.
        - You need background information, historical context, or general knowledge on a subject.
        - The model lacks sufficient information or needs a trusted source to verify an answer.

        This tool helps enhance responses by retrieving verified content from Wikipedia whenever 
        additional context is required.
        """
        return Tool(
            name="WikipediaSearch",
            func=lambda query: self.retrieve(query),
            description="Searches Wikipedia for factual and well-sourced information. Use this when asked, or when the model needs background knowledge, historical context, or a trusted reference."
        )