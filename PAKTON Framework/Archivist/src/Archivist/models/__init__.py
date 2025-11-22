"""
Description:
Models module initialization. Exports LLM factory functions and similarity checking utilities
for OpenAI, Bedrock, and local models.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""

from .llm import get_llm
from .bert import similarity_check

__all__ = ["get_llm", "similarity_check"]