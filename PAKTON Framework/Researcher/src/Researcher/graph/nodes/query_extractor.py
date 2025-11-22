"""
Description:
Query extraction and refinement node for the Researcher agent. Processes user queries
to extract and optimize search terms, determine tool requirements, and route queries
to appropriate retrieval tools with retry logic and error handling.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from typing import Dict, Any

from Researcher.types import RetrievalState, SearchQuery
from Researcher.models import get_default_llm
from Researcher.utils import SEARCH_QUERY_PROMPT
from langchain_core.messages import AIMessage

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(10),  # Retry up to 3 times
    wait=wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff
    retry=retry_if_exception_type(ValueError),  # Retry only on ValueError
    reraise=True  # Raise the error after max retries
)
def extract_query(state: RetrievalState, tools) -> RetrievalState:
    """Extract the search query from the input state.
    
    This function requires a query to be explicitly provided in the state.
    
    Args:
        state: Current state of the agent
        
    Returns:
        Updated state with the extracted query
        
    Raises:
        ValueError: If no query is provided in the state
    """
    if not state.get("query"):
        raise ValueError("No query provided in the state. A search query is required.")
    
    original_query = state["query"]
    instructions = state.get("instructions", "")
    # Get LLM with node-specific configuration
    llm = get_default_llm(node_name="query_extractor")
    # llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=True)
    llm_with_tools = llm.bind_tools(tools)

    # Check if the LLM supports structured output
    # if hasattr(llm, "with_structured_output"):
    #     try:
    #         restructured_query = llm.with_structured_output(SearchQuery).invoke(
    #             [SEARCH_QUERY_PROMPT.format(query=original_query)]
    #         )
    #         return {"query": restructured_query.search_query}  # Extract structured output content
    #     except Exception as e:
    #         print(f"Warning: Structured output failed, falling back to normal invocation. Error: {e}")

    # If structured output is not supported or fails, use regular invocation
    # restructured_query = llm.invoke([SEARCH_QUERY_PROMPT.format(query=original_query)])
    response = llm_with_tools.invoke([SEARCH_QUERY_PROMPT.format(query=original_query, instructions=instructions)])
    
    # Check if the response contains a tool call
    if response.tool_calls:
        first_tool_call = response.tool_calls[0]
        first_argument_value = next(iter(first_tool_call.get("args", {}).values()), None)
        if first_argument_value:
            state["query"] = first_argument_value
    else:
        raise ValueError("No tool used from the response.")

    state["messages"] = [response]
    
    return state
