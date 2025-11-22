"""
Description:
Graph node that formats and saves the complete interrogation conversation between the legal interrogator and researcher for final report generation.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from Interrogator.types import InterrogationState
from langchain_core.messages import get_buffer_string

from Interrogator.utils import format_conversation

def save_interrogation(state: InterrogationState):
    """Save interrogation with structured message formatting"""

    # Get messages
    messages = state["messages"]

    # Save to interrogation key
    return {"interrogation": format_conversation(messages, "Legal Interrogator", "Legal Researcher")}