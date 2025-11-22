"""
Description:
LightRAG retriever implementation for advanced graph-based RAG information retrieval.
Connects to a LightRAG server to perform hybrid retrieval combining local and global
context using knowledge graphs for more effective search results.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
import traceback
import requests
import json
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain.tools import Tool

from .base import BaseRetriever
from Researcher.utils import logger
from Researcher.utils import config
from Researcher.utils.lightrag_parser import parse_lightrag_response

class LightRAGRetriever(BaseRetriever):
    """
    A retriever that uses LightRAG for advanced RAG-based information retrieval.
    
    This retriever connects to a LightRAG server to perform hybrid retrieval
    combining local and global context for more effective search results.
    
    Features:
    - **Multiple retrieval modes**: local, global, or mixed
    - **Configurable response formats**: single or multiple paragraphs
    - **Token limit controls**: for optimizing context size
    
    Attributes:
        lightrag_config (dict): Configuration settings for LightRAG retrieval
        base_url (str): The base URL for the LightRAG API
        mode (str): Retrieval mode (local, global, or mix)
        top_k (int): Number of documents to retrieve
        response_type (str): Format of the response
        max_token (int): Maximum tokens for context
        only_need_context (bool): Whether to only return context documents
        only_need_prompt (bool): Whether to only return the prompt
        parser_config (dict): Configuration for parsing the response
    """

    def __init__(self):
        """
        Initializes the LightRAG retriever using parameters from config.yaml.
        
        - **Server Connection**: Connects to the LightRAG service API
        - **Configurable Settings**: Loads retrieval parameters from config
        - **Error Handling**: Validates settings and connection availability
        
        Raises:
            ValueError: If required settings are missing
            Exception: If an error occurs during initialization
        """
        try:
            # Load LightRAG retriever settings from config.yaml
            self.lightrag_config = config.get("retrievers.lightrag", {})
            
            # API connection settings - allow environment variable override
            self.base_url = self.lightrag_config.get("base_url", os.environ.get("LIGHTRAG_BASE_URL", "http://localhost:9621"))
            
            # Retrieval settings
            self.mode = self.lightrag_config.get("mode", "mix")  # local, global, or mix
            self.top_k = self.lightrag_config.get("top_k", 10)
            self.response_type = self.lightrag_config.get("response_type", "Single Paragraph")
            self.max_token = self.lightrag_config.get("max_token", 4000)
            
            # New settings for context and prompt control
            self.only_need_context = self.lightrag_config.get("only_need_context", True)
            self.only_need_prompt = self.lightrag_config.get("only_need_prompt", False)
            
            # Parser configuration
            self.parser_config = self.lightrag_config.get("parser", {})
            
            # Validate the connection to the LightRAG server
            self._check_connection()
            
            logger.info(f"Initializing LightRAGRetriever with base URL: {self.base_url}")
            logger.info(f"LightRAGRetriever configuration: mode={self.mode}, top_k={self.top_k}, response_type={self.response_type}")
            logger.info(f"Context settings: only_need_context={self.only_need_context}, only_need_prompt={self.only_need_prompt}")

        except Exception as e:
            logger.error("Error initializing LightRAGRetriever: %s", str(e))
            logger.debug(traceback.format_exc())
            raise
    
    def _check_connection(self):
        """Check if the LightRAG server is accessible."""
        try:
            response = requests.get(f"{self.base_url}/documents")
            response.raise_for_status()
            logger.info("Successfully connected to LightRAG server")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Unable to connect to LightRAG server: {e}")
            # Not raising an exception here to allow for graceful degradation

    @property
    def name(self) -> str:
        """
        Returns the unique name identifier of this retriever.
        
        Returns:
            str: The retriever's name identifier.
        """
        return "lightrag_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves information from LightRAG using the specified query.
        
        Args:
            query (str): The search query
            **kwargs: Additional parameters that can override default settings
            
        Returns:
            List[Document]: Retrieved documents with metadata
        """
        try:
            logger.info(f"Retrieving from LightRAG for query: {query}")
            
            # Check for specific LightRAG configuration in kwargs
            lightrag_specific_config = kwargs.get("lightrag_retriever", {})
            
            # Override settings with priority: 
            # 1. lightrag_retriever specific config
            # 2. general kwargs
            # 3. default config values
            mode = lightrag_specific_config.get("mode", kwargs.get("mode", self.mode))
            top_k = lightrag_specific_config.get("top_k", kwargs.get("top_k", self.top_k))
            response_type = lightrag_specific_config.get("response_type", kwargs.get("response_type", self.response_type))
            max_token = lightrag_specific_config.get("max_token", kwargs.get("max_token", self.max_token))
            only_need_context = lightrag_specific_config.get("only_need_context", kwargs.get("only_need_context", self.only_need_context))
            only_need_prompt = lightrag_specific_config.get("only_need_prompt", kwargs.get("only_need_prompt", self.only_need_prompt))
            
            # Get parser config (merging kwargs and defaults)
            parser_config = lightrag_specific_config.get("parser", kwargs.get("parser", self.parser_config))
            
            # Prepare the query payload
            payload = {
                "query": query,
                "mode": mode,
                "only_need_context": only_need_context,
                "only_need_prompt": only_need_prompt,
                "response_type": response_type,
                "top_k": top_k,
                "max_token_for_text_unit": max_token,
                "max_token_for_global_context": max_token,
                "max_token_for_local_context": max_token,
                "history_turns": 0
            }
            
            logger.debug(f"Sending LightRG query with parameters: mode={mode}, top_k={top_k}, response_type={response_type}")
            logger.debug(f"Context parameters: only_need_context={only_need_context}, only_need_prompt={only_need_prompt}")
            
            # Send the query to LightRAG
            response = requests.post(f"{self.base_url}/query", json=payload)
            response.raise_for_status()
            results = response.json()

            logger.debug(f"LightRAG response: {results}")
            
            # Parse the response into Document objects using the parser
            documents = parse_lightrag_response(results, parser_config)
            
            logger.info(f"Retrieved {len(documents)} documents from LightRAG")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving from LightRAG: {str(e)}")
            logger.debug(traceback.format_exc())
            return []

    @property
    def tool(self) -> Tool:
        """
        Return the retriever as a tool.

        Returns:
            Tool: LangChain Tool interface for this retriever
        """
        return Tool(
            name="LightRAGSearch",
            func=lambda query: self.retrieve(query),
            description=(
                "Use LightRAGSearch to retrieve contextual information from a wide range of documents. "
                "This tool is ideal when answering complex or exploratory questions that require synthesizing insights "
                "from multiple sources. It excels at handling questions involving relationships across documents, "
                "temporal sequences, or high-level summaries. Invoke this tool when the user query goes beyond "
                "a single document's scope and requires global understanding or cross-document analysis."
            )
        )