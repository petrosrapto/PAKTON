"""
Description:
Simple usage example of the Archivist agent. Demonstrates basic configuration
and indexing functionality with vector database backend.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""

from src.Archivist.agent import Archivist

# Configure the agent
config = {
    "enable_vectordb": True,
    "run_name": "Example Index"
}

# Initialize the archivist agent
archivist = Archivist(config)

# Example 1: Direct index
print("\n=== Example 1: Direct Index ===\n")
results = archivist.index()