"""
Description:
LightRAG response parser utility for processing LightRAG service responses.
Provides functions to parse JSON responses, extract content from markdown blocks,
and convert LightRAG outputs into LangChain Document objects for the Researcher agent.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from langchain_core.documents import Document

# Import directly from logging module to avoid circular imports
from Researcher.utils.logging import logger


def extract_json_from_text(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract JSON content from a text block that may be wrapped in markdown code blocks.
    
    Args:
        text (str): Text containing JSON data, possibly within markdown code blocks
        
    Returns:
        Optional[List[Dict[str, Any]]]: Parsed JSON data or None if parsing fails
    """
    try:
        # Try to extract JSON between markdown json code blocks
        json_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
        if json_match:
            json_content = json_match.group(1).strip()
        else:
            # Assume the entire text might be JSON
            json_content = text.strip()
        
        # Try to parse the extracted content
        return json.loads(json_content)
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse JSON from text: {e}")
        return None


def parse_lightrag_response(
    response: Dict[str, Any], 
    config: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Parse a LightRAG response into a list of Document objects.
    
    Args:
        response (Dict[str, Any]): The LightRAG response
        config (Optional[Dict[str, Any]]): Configuration for parsing
            - include_entities (bool): Whether to include entity information (default: True)
            - include_relationships (bool): Whether to include relationship information (default: True)
            - include_sources (bool): Whether to include source documents (default: True)
            - include_vector_context (bool): Whether to include vector context (default: True)
            - max_entities (int): Maximum number of entities to include (default: 10)
            - max_relationships (int): Maximum number of relationships to include (default: 10)
            - max_sources (int): Maximum number of sources to include (default: 5)
            
    Returns:
        List[Document]: List of Document objects extracted from the response
    """
    if config is None:
        config = {}
    
    # Set default configurations
    include_entities = config.get("include_entities", True)
    include_relationships = config.get("include_relationships", True)
    include_sources = config.get("include_sources", True)
    include_vector_context = config.get("include_vector_context", True)
    max_entities = config.get("max_entities", 10)
    max_relationships = config.get("max_relationships", 10)
    max_sources = config.get("max_sources", 5)
    
    documents = []
    
    # Parse the response content
    if "response" not in response:
        logger.warning("Invalid LightRAG response: 'response' field missing")
        return []
    
    response_text = response["response"]
    
    # Process entities if included
    if include_entities and "-----Entities-----" in response_text:
        entities_section = re.search(r'-----Entities-----\s*\n(.*?)(?=-----Relationships-----|$)', 
                                    response_text, re.DOTALL)
        if entities_section:
            entities_text = entities_section.group(1).strip()
            entities_data = extract_json_from_text(entities_text)
            
            if entities_data:
                # Take only up to max_entities
                for i, entity in enumerate(entities_data[:max_entities]):
                    # Create a document for each entity
                    entity_content = (
                        f"Entity: {entity.get('entity', 'Unknown')}\n"
                        f"Type: {entity.get('type', 'Unknown')}\n"
                        f"Description: {entity.get('description', '')}"
                    )
                    
                    doc = Document(
                        page_content=entity_content,
                        metadata={
                            "source": "LightRAG Knowledge Graph - Entity",
                            "entity_id": entity.get("id"),
                            "entity_name": entity.get("entity"),
                            "entity_type": entity.get("type"),
                            "entity_rank": entity.get("rank"),
                            "file_path": entity.get("file_path", "").split("<SEP>")[0] if entity.get("file_path") else "",
                            "content_type": "entity"
                        }
                    )
                    documents.append(doc)
    
    # Process relationships if included
    if include_relationships and "-----Relationships-----" in response_text:
        relationships_section = re.search(r'-----Relationships-----\s*\n(.*?)(?=-----Sources-----|$)', 
                                         response_text, re.DOTALL)
        if relationships_section:
            relationships_text = relationships_section.group(1).strip()
            relationships_data = extract_json_from_text(relationships_text)
            
            if relationships_data:
                # Take only up to max_relationships
                for i, relationship in enumerate(relationships_data[:max_relationships]):
                    # Create a document for each relationship
                    relationship_content = (
                        f"Relationship: {relationship.get('source', 'Unknown')} → {relationship.get('target', 'Unknown')}\n"
                        f"Description: {relationship.get('description', '')}"
                    )
                    
                    doc = Document(
                        page_content=relationship_content,
                        metadata={
                            "source": "LightRAG Knowledge Graph - Relationship",
                            "relationship_id": relationship.get("id"),
                            "source_entity": relationship.get("source"),
                            "target_entity": relationship.get("target"),
                            "relationship_rank": relationship.get("rank"),
                            "file_path": relationship.get("file_path", "").split("<SEP>")[0] if relationship.get("file_path") else "",
                            "content_type": "relationship"
                        }
                    )
                    documents.append(doc)
    
    # Process sources if included
    if include_sources and "-----Sources-----" in response_text:
        sources_section = re.search(r'-----Sources-----\s*\n(.*?)(?=-----Vector Context-----|$)', 
                                   response_text, re.DOTALL)
        if sources_section:
            sources_text = sources_section.group(1).strip()
            sources_data = extract_json_from_text(sources_text)
            
            if sources_data:
                # Take only up to max_sources
                for i, source in enumerate(sources_data[:max_sources]):
                    # Extract content and clean up formatting
                    content = source.get("content", "")
                    # Remove "--- ORIGINAL SPAN OF THE DOCUMENT ---" and "------" markers
                    content = re.sub(r'---\s*ORIGINAL SPAN OF THE DOCUMENT\s*---', '', content)
                    content = re.sub(r'------', '', content)
                    content = content.strip()
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "LightRAG Sources",
                            "source_id": source.get("id"),
                            "file_path": source.get("file_path", ""),
                            "content_type": "source"
                        }
                    )
                    documents.append(doc)
    
    # Process vector context if included
    if include_vector_context and "-----Vector Context-----" in response_text:
        vector_context_section = re.search(r'-----Vector Context-----\s*\n(.*?)(?=$)', 
                                          response_text, re.DOTALL)
        if vector_context_section:
            vector_context = vector_context_section.group(1).strip()
            
            # Split by "--New Chunk--" marker
            chunks = vector_context.split("--New Chunk--")
            
            for i, chunk in enumerate(chunks):
                # Extract file path and creation time
                file_path_match = re.search(r'File path: (.*?)\n', chunk)
                created_at_match = re.search(r'\[Created at: (.*?)\]', chunk)
                
                file_path = file_path_match.group(1) if file_path_match else "Unknown"
                created_at = created_at_match.group(1) if created_at_match else "Unknown"
                
                # Clean up content
                content = re.sub(r'--- ORIGINAL SPAN OF THE DOCUMENT ---', '', chunk)
                content = re.sub(r'------', '', content)
                content = re.sub(r'\[Created at: .*?\]', '', content)
                content = re.sub(r'File path: .*?\n', '', content)
                content = content.strip()
                
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "LightRAG Vector Context",
                            "file_path": file_path,
                            "created_at": created_at,
                            "chunk_index": i,
                            "content_type": "vector_context"
                        }
                    )
                    documents.append(doc)
    
    # If context field is present (newer API version), use it directly
    if "context" in response and isinstance(response["context"], list):
        for i, ctx in enumerate(response["context"]):
            metadata = {
                "source": ctx.get("source", "LightRAG Direct Context"),
                "score": ctx.get("score", 0.0),
                "index": i,
                "document_id": ctx.get("id", f"lightrag-doc-{i}"),
                "content_type": "direct_context"
            }
            
            doc = Document(
                page_content=ctx.get("content", ""),
                metadata=metadata
            )
            documents.append(doc)
    
    logger.info(f"Parsed LightRAG response into {len(documents)} documents")
    return documents