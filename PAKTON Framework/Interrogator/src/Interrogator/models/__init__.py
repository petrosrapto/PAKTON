"""
Description:
Model interfaces module that provides access to various LLM providers and machine learning components for the Interrogator agent.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""

from .llm import get_default_llm
from .bert import similarity_check

__all__ = ["get_default_llm", "similarity_check"]