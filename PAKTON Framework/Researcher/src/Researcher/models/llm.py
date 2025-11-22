"""
Description:
Large Language Model factory and management module. Provides unified interface for 
accessing different LLM providers (OpenAI, AWS Bedrock, Google) with support for 
node-specific model configurations and fallback to default models.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
from Researcher.utils import config, logger
from .bedrock import get_bedrock_llm
from .openai import get_openai_llm
from .google import get_google_llm

def get_default_llm(node_name=None):
    """
    Returns the LLM based on configuration, with support for node-specific models.

    Args:
        node_name (str, optional): Name of the node requesting the LLM. 
                                  If provided, will look for node-specific model config.

    The configuration should be provided in the "models" section:
        - "models.default" for the default model
        - "models.{node_name}" for node-specific models
    
    Each model config should have keys:
        - "API": either "openai", "bedrock", or "google"
        - "model_id": the model ID to use
        - "args": dictionary containing model parameters like max_tokens, temperature, etc.

    Returns:
        An instance of the configured LLM (ChatOpenAI, BedrockLLM, or ChatGoogleGenerativeAI).
    """
    # First, try to get a node-specific model if node_name is provided
    if node_name:
        node_models_config = config.get(f"models.{node_name}")
        if node_models_config:
            logger.info(f"Using node-specific model for {node_name}")
            return _create_llm_from_config(node_models_config, node_name)
    
    # Fall back to the default model config
    models_config = config.get("models.default", {})
    return _create_llm_from_config(models_config, "default")

def _create_llm_from_config(models_config, config_name):
    """Helper function to create an LLM from a config dictionary"""
    api = models_config.get("API", "").lower()
    if not api:
        raise ValueError(f"The {config_name} models config must include an 'API'.")
    
    model_id = models_config.get("model_id")
    if not model_id:
        raise ValueError(f"The {config_name} models config must include a 'model_id'.")

    args = models_config.get("args", {})  # Extract args from config
    endpoint_url = models_config.get("endpoint_url", None)  # Extract endpoint_url from config

    logger.debug(f"Creating LLM for {config_name} using {api} model: {model_id}")

    if api == "bedrock":
        return get_bedrock_llm(model_id, **args)
    elif api == "openai":
        return get_openai_llm(model_id, endpoint_url=endpoint_url, **args)
    elif api == "google":
        return get_google_llm(model_id, **args)
    else:
        raise ValueError(f"Unsupported API '{api}'. Please choose either 'openai', 'bedrock', or 'google'.")