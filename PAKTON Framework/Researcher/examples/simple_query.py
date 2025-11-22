"""
Description:
Simple usage example demonstrating how to use the Researcher agent for information
retrieval. Shows basic configuration, initialization, and query execution with
multiple retrieval sources including hybrid retrieval methods.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""

from Researcher import Researcher

# Configure the agent
# this config sets the nodes of the graph, while quering you can pick a subset
# of the retrievers to use
config = {
    "enable_web": False,
    "enable_wikipedia": False, # wikipedia retriever returns some times rubbish
    "enable_vectordb": False,  # We don't have a vector db for this example
    "enable_bm25": False,
    "enable_hybrid": True,
    "run_name": "Example Search"
}

# Initialize the researcher agent
researcher = Researcher(config)

# Example 1: Direct query
print("\n=== Example 1: Direct Query ===\n")
results = researcher.search(
    query="models trained in ContractNLI"
    # query = "Large language models (LLMs) like GPT-4, BERT, and LLaMA"
)
print("Response:")
print(results.get("response", "No response generated"))