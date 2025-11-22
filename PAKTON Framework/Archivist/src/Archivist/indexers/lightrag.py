"""
Description:
LightRAG indexer implementation. Uploads and indexes documents using a LightRAG server,
with support for document clearing, status polling, and batch processing.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
import traceback
import time
import tempfile
import requests
import json
from typing import List, Dict, Any
from langchain_core.documents import Document

from .base import BaseIndexer
from Archivist.utils import config, logger

class LightRAGIndexer(BaseIndexer):
    """
    Indexer that uses LightRAG for document indexing.

    This indexer uploads documents to a LightRAG server for processing and indexing.

    Attributes:
        lightrag_config (dict): Configuration settings for LightRAG.
        base_url (str): Base URL for the LightRAG API.
    """

    def __init__(self):
        """Initialize the LightRAG indexer using parameters from config.yaml or environment variables."""
        try:
            # Load LightRAG configuration from config.yaml
            self.lightrag_config = config.get("indexers.lightrag", {})
            
            # Set the base URL from config or environment variable or use default
            self.base_url = self.lightrag_config.get("base_url", os.environ.get("LIGHTRAG_BASE_URL", "http://localhost:9621"))
            
            # Other configuration options
            self.clear_existing = self.lightrag_config.get("clear_existing", True)
            self.max_polling_time = self.lightrag_config.get("max_polling_time", 300)
            self.polling_interval = self.lightrag_config.get("polling_interval", 2)
            
            logger.info("Initializing LightRAGIndexer with base URL: %s", self.base_url)
            logger.info("LightRAGIndexer configuration: clear_existing=%s, max_polling_time=%s", 
                       self.clear_existing, self.max_polling_time)
            logger.info("LightRAGIndexer initialized successfully.")

        except Exception as e:
            logger.error("Error initializing LightRAGIndexer: %s", str(e))
            logger.debug(traceback.format_exc())

    @property
    def name(self) -> str:
        """Return the unique name of this indexer."""
        return "lightrag"

    def _poll_pipeline_status(self, max_polling_time=None, polling_interval=None):
        """
        Poll the pipeline status until processing is complete or timeout is reached.
        
        Args:
            max_polling_time (int): Maximum polling time in seconds (defaults to config value)
            polling_interval (int): Time between status checks in seconds (defaults to config value)
            
        Returns:
            dict: The final pipeline status or None if timeout is reached
        """
        pipeline_status_url = f"{self.base_url}/documents/pipeline_status"
        start_time = time.time()
        
        # Use parameters or fall back to config values
        max_polling_time = max_polling_time or self.max_polling_time
        polling_interval = polling_interval or self.polling_interval
        
        logger.info(f"Polling LightRAG pipeline status (timeout: {max_polling_time}s, interval: {polling_interval}s)...")
        
        while time.time() - start_time < max_polling_time:
            try:
                # Get the current pipeline status
                status_response = requests.get(pipeline_status_url)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                # Check if pipeline is busy
                if status_data.get('busy', False):
                    logger.info(f"Pipeline busy: {status_data.get('job_name', 'Unknown job')} - {status_data.get('latest_message', '')}")
                    logger.info(f"Progress: Batch {status_data.get('cur_batch', 0)}/{status_data.get('batchs', 0)}")
                else:
                    logger.info("Pipeline processing completed!")
                    return status_data
                    
                # Wait before checking again
                time.sleep(polling_interval)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling pipeline status: {e}")
                return None
        
        logger.warning(f"Max polling time ({max_polling_time} seconds) exceeded.")
        return None

    def _upload_document(self, file_path):
        """
        Upload a document to the LightRAG server.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            dict: The response from the upload endpoint
        """
        upload_url = f"{self.base_url}/documents/upload"
        
        # Prepare the file for upload
        with open(file_path, "rb") as file_content:
            files = {"file": (os.path.basename(file_path), file_content, "text/plain")}
            
            try:
                logger.info(f"Uploading document to LightRAG: {os.path.basename(file_path)}")
                upload_response = requests.post(upload_url, files=files)
                upload_response.raise_for_status()
                
                try:
                    return upload_response.json()
                except json.JSONDecodeError:
                    return {"text": upload_response.text}
            except requests.exceptions.RequestException as e:
                logger.error(f"Error uploading document to LightRAG: {e}")
                raise

    def _delete_documents(self, document_ids=None):
        """
        Delete documents from the LightRAG server.
        
        Args:
            document_ids (list, optional): List of document IDs to delete. 
                                          If None, attempts to delete all documents.
                                          
        Returns:
            dict: The response from the delete endpoint
        """
        delete_docs_url = f"{self.base_url}/documents"
        
        payload = {}
        if document_ids:
            payload["document_ids"] = document_ids
        
        try:
            logger.info(f"Deleting documents from LightRAG: {document_ids if document_ids else 'ALL'}")
            delete_response = requests.delete(delete_docs_url, json=payload if document_ids else None)
            delete_response.raise_for_status()
            
            try:
                return delete_response.json()
            except json.JSONDecodeError:
                return {"text": delete_response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting documents from LightRAG: {e}")
            raise

    def _get_documents_status(self):
        """
        Get the status of all documents in the LightRAG server.
        
        Returns:
            dict: The response with document statuses
        """
        docs_url = f"{self.base_url}/documents"
        
        try:
            logger.info("Fetching document statuses from LightRAG")
            docs_response = requests.get(docs_url)
            docs_response.raise_for_status()
            return docs_response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching document statuses from LightRAG: {e}")
            raise

    def index(self, docs: List[Document], **kwargs) -> None:
        """
        Index documents into LightRAG.

        Args:
            docs (List[Document]): A list of LangChain Document objects to be indexed.
            **kwargs: Additional parameters that can override config values.
        """
        try:
            logger.info("Indexing %d documents into LightRAG...", len(docs))
            
            # Use kwargs first, then config values, then defaults
            clear_existing = kwargs.get("clear_existing", self.clear_existing)
            max_polling_time = kwargs.get("max_polling_time", self.max_polling_time)
            polling_interval = kwargs.get("polling_interval", self.polling_interval)
            
            # Delete existing documents if requested
            if clear_existing:
                logger.info("Deleting all existing documents before indexing...")
                delete_result = self._delete_documents()
                time.sleep(2)  # Wait for deletion to process
                logger.info(f"Delete result: {delete_result}")

            # Process each document
            for i, doc in enumerate(docs):
                logger.info(f"Processing document {i+1}/{len(docs)}")
                
                # Create a temporary file with the document text
                file_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp_file:
                        file_path = tmp_file.name
                        tmp_file.write(doc.page_content)
                    
                    # Upload the document
                    upload_response = self._upload_document(file_path)
                    logger.info(f"Document uploaded successfully: {upload_response}")
                    time.sleep(2)  # Wait a bit to allow processing to start
                    
                finally:
                    # Clean up temporary file
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
            
            # Poll until processing is complete
            pipeline_status = self._poll_pipeline_status(max_polling_time=max_polling_time, polling_interval=polling_interval)
            if not pipeline_status:
                logger.error("Document processing timed out or failed")
                return
                
            # Check the document status
            docs_status = self._get_documents_status()
            logger.info(f"Document processing completed with status: {docs_status}")

        except Exception as e:
            logger.error("Error indexing documents to LightRAG: %s", str(e))
            logger.debug(traceback.format_exc())