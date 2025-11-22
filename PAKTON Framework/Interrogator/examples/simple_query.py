"""
Description:
Simple usage example demonstrating how to initialize and use the Interrogator agent for basic legal interrogation tasks.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""

from src.Interrogator.agent import Interrogator

# Configure the agent
config = {
    "run_name": "Example Interrogation"
}

# Initialize the agent
interrogator = Interrogator(config)

# Example 1: Direct index
print("\n=== Example 1: Direct Interrogation ===\n")
results = interrogator.index()