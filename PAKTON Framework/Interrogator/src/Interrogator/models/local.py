"""
Description:
Local model interface for hosting Hugging Face models with caching support, designed to work with VLLM for efficient local LLM deployment.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
import traceback
# from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
# from transformers import pipeline
from Interrogator.utils import config  

# Global variable to store the cached model
_cached_llm = None

## IT IS BETTER TO USE VLLM FOR LOCAL LLMS INSTEAD OF DOWNLOADING DIRECTLY FROM HUGGINGFACE
## THEN WHEN LOCAL API IS PICKED, CALL TO THE CORRESPONDING API WILL BE MADE

def get_local_llm(model_id: str, **kwargs):
    """
    Returns an instance of a locally hosted Hugging Face LLM.

    Ensures the model is only initialized once and cached for reuse.

    Args:
        model_id (str): The Hugging Face model repo ID.
        **kwargs: Additional parameters for model inference.

    Returns:
        ChatHuggingFace: Configured instance of a locally running Hugging Face LLM.
    """
    global _cached_llm
    return None

    # If the model is already loaded, return the cached instance
    if _cached_llm is not None:
        return _cached_llm

    try:
        # Default model parameters (merged with additional args)
        default_args = {"task": "text-generation"}
        
        # Update with provided kwargs (if any)
        model_params = {**default_args, **kwargs}

        # Load model locally with parameters
        local_pipeline = pipeline(
            task=model_params.pop("task"), 
            model=model_id,
            **model_params  # Pass additional parameters to the pipeline
        )
        
        _cached_llm = ChatHuggingFace(llm=HuggingFacePipeline(pipeline=local_pipeline))  # Cache the instance
        return _cached_llm
    
    except Exception as e:
        print("Error initializing the local LLM:", e)
        traceback.print_exc()
        raise
