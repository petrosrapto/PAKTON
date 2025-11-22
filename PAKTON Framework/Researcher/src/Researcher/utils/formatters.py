"""
Description:
Formatting and sanitization utilities for the Researcher agent. Provides functions
for document formatting, HTML/XML content cleaning, JSON text extraction, and
various text processing operations for safe content handling.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from typing import Dict, Any, List, Optional, Union

from langchain_core.documents import Document
import re
import bleach

def sanitize_with_bleach(s):
    """
    Use bleach library to clean HTML/XML-like content from strings.
    """
    # Strip all HTML tags
    return bleach.clean(s, tags=[], strip=True)

def extract_texts_from_json(raw_json_string):
    """Extract text fields from JSON with potentially invalid quote escaping."""
    
    # Method 1: Using regex directly (most robust for this specific case)
    # This finds all text fields regardless of JSON validity
    text_pattern = re.compile(r'"text":\s*"(.*?)(?="\s*})', re.DOTALL)
    matches = text_pattern.findall(raw_json_string)
    
    if matches:
        # Clean up any potential issues from the regex extraction
        texts = [m.replace('\n', ' ').strip() for m in matches]
        
        # Create a properly structured JSON object
        structured_data = {
            "spans": [{"text": text} for text in texts]
        }
        
        return structured_data
    

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