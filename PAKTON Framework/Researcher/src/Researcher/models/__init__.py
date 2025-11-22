"""
Description:
Model interfaces and factory functions for large language models and ML components.
Provides unified access to various LLM providers (OpenAI, Bedrock, Google) through
a common interface with configuration-based selection.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""

from .llm import get_default_llm

__all__ = ["get_default_llm"]