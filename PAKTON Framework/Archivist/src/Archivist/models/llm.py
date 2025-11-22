"""
Description:
Default LLM factory function. Dynamically selects and returns the appropriate LLM instance
(OpenAI, Bedrock, or local) based on configuration settings.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
from Archivist.utils import config as default_config
from Archivist.utils import get_required_config
from .bedrock import get_bedrock_llm
from .openai import get_openai_llm
from .local import get_local_llm

from typing import Optional, Dict, Any

def get_llm(config: Optional[Dict[str, Any]] = {}):
    """
    Returns the LLM based on configuration.

    The configuration should be provided in the "models" section.
    
    Each model config should have keys:
        - "API": either "openai", "bedrock", "google"
        - "model_id": the model ID to use
        - "args": dictionary containing model parameters like max_tokens, temperature, etc.

    Args:
        config: Optional configuration dict. If not provided or missing required keys,
                falls back to default_config from config.yaml
        
    Returns:
        An instance of the configured LLM (ChatOpenAI, BedrockLLM, ChatGoogleGenerativeAI).
    """
    
    if config == {}:
        # Fall back to the default model config if no config is provided
        models_config = default_config.get_required("models")
    else:
        models_config = config

    api = get_required_config("API", models_config).lower()
    model_id = get_required_config("model_id", models_config)
    args = models_config.get("args", {})  # Extract args from config

    if api == "bedrock":
        return get_bedrock_llm(model_id, **args)
    elif api == "openai":
        return get_openai_llm(model_id, **args)
    elif api == "local":
        return get_local_llm(model_id, **args)
    else:
        raise ValueError(f"Unsupported API '{api}'. Please choose either 'openai' or 'bedrock' or 'local'.")