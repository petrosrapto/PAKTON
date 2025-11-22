"""
Description:
Document parsing node for the graph workflow. Handles parsing and splitting of documents
using either naive or structural parsing strategies based on configuration.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from Archivist.types import IndexState

from Archivist.parser import NaiveDocumentSplitterAndParser, StructuralParser

from Archivist.utils import config
import logging

parser_config = config.get("parser", {})
type = parser_config.get("type", "naive")

def parse_and_split(state: IndexState) -> IndexState:

    # Extract file path from the state
    filePath = state.get("filePath", None)
    if not filePath:
        raise ValueError("No filePath found in state. Please provide a file path.")

    if type == "naive":
        naive_config = parser_config.get("naive", {})
        chunk_size = naive_config.get("chunk_size", 1000)
        chunk_overlap = naive_config.get("chunk_overlap", 200)
        parser = NaiveDocumentSplitterAndParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = parser.parse_document(filePath)
    elif type == "structural":
        try:
            parser = StructuralParser()
            docs = parser.parse_document(filePath)
        except Exception as e:
            logging.warning(f"Structural parser failed with error: {str(e)}. Falling back to naive parser.")
            # Fallback to naive parser
            parser = NaiveDocumentSplitterAndParser(chunk_size=1000, chunk_overlap=200)
            docs = parser.parse_document(filePath)
    
    return { "splitDocs": docs }