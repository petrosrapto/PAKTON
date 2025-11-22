"""
Description:
Utility functions and helpers for the Researcher agent.
Provides configuration management, logging, formatting, prompts,
and various helper functions used across the application.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""

from .formatters import format_documents, sanitize_with_bleach, extract_texts_from_json
from .prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_HUMAN_PROMPT,
    SEARCH_QUERY_PROMPT
)
from .lightrag_parser import parse_lightrag_response

from .logging import logger
from .config import config

__all__ = [
    "format_documents",
    "RAG_SYSTEM_PROMPT",
    "RAG_HUMAN_PROMPT",
    "SEARCH_QUERY_PROMPT",
    "logger",
    "config",
    "sanitize_with_bleach",
    "extract_texts_from_json",
    "parse_lightrag_response"
]