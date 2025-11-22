"""
Description:
AWS Bedrock language model integration for the Researcher agent. Provides factory function
to create and configure ChatBedrock instances with support for various Bedrock foundation models.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
from langchain_aws import ChatBedrock
from Researcher.utils import config  

def get_bedrock_llm(model_id: str, **kwargs):
    """
    Returns an instance of AWS Bedrock LLM with additional parameters.

    Requires the following environment variables to be set:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION
    
    Args:
        model_id (str): The Bedrock model ID to use.
        **kwargs: Additional arguments (e.g., max_tokens, temperature, top_p).

    Returns:
        ChatBedrock: Configured instance of AWS Bedrock LLM.
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION_NAME")
    
    if not aws_access_key_id or not aws_secret_access_key or not region:
        raise ValueError("AWS credentials are not set in environment variables.")

    return ChatBedrock(
        model_id=model_id,
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        beta_use_converse_api=True,
        **kwargs
    )