"""
Description:
Web search retriever implementation using Tavily API for real-time information retrieval.
Integrates with external search engines to fetch up-to-date web content and converts
results into structured LangChain Document objects for the Researcher agent.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10

Technical Implementation:
Web Retriever

### Theoretical Background:
A **web retriever** allows AI models to **fetch real-time information** from the web 
by integrating with external search engines like **Tavily, SerpAPI, Google, or Bing**. 
Unlike static knowledge sources (e.g., local databases, vector search), web retrieval 
provides **up-to-date and contextually relevant** information.

### How Web Retrieval Works:
1. **User Query**:
   - The user provides a query (e.g., "Latest AI research papers").
   
2. **Search Engine API Integration**:
   - The retriever sends the query to a web search API (e.g., **Tavily, SerpAPI**).
   - The API performs a search and retrieves **top-ranked web pages**.

3. **Processing Search Results**:
   - The retriever extracts **content, URLs, and metadata** from the results.
   - Converts them into **LangChain Document objects** for structured retrieval.

4. **Use Cases**:
   - **Real-time knowledge retrieval** (e.g., "Current stock prices").
   - **News and event tracking** (e.g., "Latest legal updates on GDPR").
   - **AI-powered research** (e.g., "New techniques in deep learning").
   - **Fact-checking and verification** (e.g., "Is X law still active?").

This module implements **web retrieval via Tavily**, allowing **real-time document retrieval** 
from the internet and structured integration with LangChain.

Author: Petros Raptopoulos (petrosrapto@gmail.com)
Date: 7.3.2025
"""

import os
import traceback
from typing import List
from langchain_core.documents import Document
from langchain_community.tools.tavily_search import TavilySearchResults

from .base import BaseRetriever
from Researcher.utils import logger  # Import the logger
from Researcher.utils import config  # Import the Config loader

from langchain.tools import Tool    

class WebRetriever(BaseRetriever):
    """
    A retriever that searches the web for information **in real-time** using Tavily or another search API.

    Instead of relying on **pre-stored knowledge**, this retriever **fetches live web results** to provide 
    the latest and most relevant information available online.

    Features:
    - **Supports Tavily Search API** for live web search.
    - **Configurable maximum results** for fine-tuned retrieval.
    - **Structured Output**: Converts web results into LangChain Document objects.

    Attributes:
        search_client_name (str): The name of the web search API being used.
        max_results (int): The maximum number of search results to retrieve.
        tavily_api_key (str): API key for accessing Tavily search.
        search_client (TavilySearchResults): The web search client instance.
    """

    def __init__(self):
        """
        Initializes the **web retriever** using parameters from `config.yaml`.

        - **Search Client**: Uses Tavily by default (can be extended for other providers).
        - **Configurable Settings**: Allows customization of search behavior.
        - **Secure API Handling**: Ensures API key validation.

        Raises:
            ValueError: If the API key is missing or an unsupported search client is specified.
            Exception: If an error occurs during initialization.
        """
        try:
            # Load web retriever settings
            web_config = config.get("retrievers.web", {})

            self.search_client_name = web_config.get("search_client", "tavily")
            self.max_results = web_config.get("max_results", 5)
            self.tavily_api_key = os.environ.get("TAVILY_API_KEY")

            # Log retriever configuration
            logger.info("Initializing WebRetriever with config: %s", web_config)

            # Validate and initialize the search client
            if self.search_client_name == "tavily":
                if not self.tavily_api_key:
                    raise ValueError("TAVILY_API_KEY is required but not set in environment or config.")
                self.search_client = TavilySearchResults(tavily_api_key=self.tavily_api_key)
            else:
                raise ValueError(f"Unsupported search client: {self.search_client_name}")

        except Exception as e:
            logger.error("Error initializing WebRetriever: %s", str(e))
            logger.debug(traceback.format_exc())

    @property
    def name(self) -> str:
        """
        Returns the unique name identifier of this retriever.

        Returns:
            str: The retriever's name identifier.
        """
        return "web_retriever"

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieves **real-time web documents** using a search engine API.

        This method:
        - Sends the **query** to an external search API (e.g., Tavily).
        - Retrieves **web pages** with metadata (e.g., URLs, titles, summaries).
        - Converts results into **LangChain Document objects** for structured retrieval.

        Args:
            query (str): The input search query.
            **kwargs: Additional parameters, such as `max_results` for limiting results.

        Returns:
            List[Document]: A **list of retrieved web documents**.

        Logs:
            - Logs query execution and retrieval success.
            - Logs the number of documents retrieved.
        """
        try:
            # Override max results if provided
            max_results = kwargs.get("max_results", self.max_results)

            logger.info("Retrieving web documents for query: %s", query)

            # Perform web search
            search_results = self.search_client.invoke({"query": query, "max_results": max_results})

            logger.info("Successfully retrieved %d web documents", len(search_results))

            # Convert search results to LangChain Document format
            documents = [
                Document(
                    page_content=doc.get("content", ""),
                    metadata={
                        "source": doc.get("url", ""),
                        "title": doc.get("title", ""),
                        "retriever": self.name
                    }
                )
                for doc in search_results
            ]

            logger.info("Documents retrieved: %s", str(documents))
            
            return documents

        except Exception as e:
            logger.error("Error retrieving from the web: %s", str(e))
            logger.debug(traceback.format_exc())
            return []

    @property
    def tool(self) -> Tool:
        """
        Returns the WebRetriever as a LangChain Tool.

        This tool allows agents to perform real-time web searches to retrieve the latest and most relevant 
        information from the internet. Use it when:
        
        - A query requires up-to-date knowledge that isn't available in the model's memory.
        - You need to verify facts or check for recent developments on a topic.
        - The model is uncertain or lacks sufficient context to provide a confident answer.

        This tool helps bridge knowledge gaps by searching the web whenever more information is needed.
        """
        return Tool(
            name="WebSearch",
            func=lambda query: self.retrieve(query),
            description="Searches the web for real-time information. Use this when the model lacks sufficient knowledge or needs the latest updates on a topic."
        )