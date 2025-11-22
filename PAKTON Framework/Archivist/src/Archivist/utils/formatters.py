"""
Description:
Formatting utilities for the Archivist agent. Provides functions to format Document objects
into structured XML-like representations with metadata for LLM consumption.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import Dict, Any, List, Optional, Union

from langchain_core.documents import Document

def format_documents(documents: List[Document]) -> str:
    """Format a list of Document objects using <Document> tags for the LLM.
    
    Args:
        documents: List of Document objects
        
    Returns:
        Formatted context string with documents in <Document> tags
    """
    if not documents:
        return "No documents were retrieved."
    
    # Format each document with <Document> tags
    formatted_docs = []
    
    for i, doc in enumerate(documents):
        # Extract metadata
        metadata = doc.metadata
        source = metadata.get("source", "")
        url = metadata.get("url", "")
        # Determine href (prioritize source, fallback to url)
        href = source if source else url

        title = metadata.get("title", "")
        retriever = metadata.get("retriever", "unknown")
        
        # Build opening tag with metadata as attributes
        opening_tag = f'<Document index="{i+1}"'
        
        if source:
            opening_tag += f' href="{href}"'
        if title:
            opening_tag += f' title="{title}"'
        if retriever:
            opening_tag += f' retriever="{retriever}"'
            
        opening_tag += "/>"
        
        # Format the complete document
        formatted_docs.append(f"{opening_tag}\n{doc.page_content}\n</Document>")
    
    # Wrap all documents between a Documents tag
    all_docs = "\n\n".join(formatted_docs)
    return f"<Documents>\n{all_docs}\n</Documents>"