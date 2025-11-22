"""
Description:
Parser module initialization. Exports document parsing implementations including
naive text splitting and structural parsing with LLM-based section extraction.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""

from .naiveParser import NaiveDocumentSplitterAndParser
from .structuralParser import StructuralParser

__all__ = ["NaiveDocumentSplitterAndParser", "StructuralParser"]