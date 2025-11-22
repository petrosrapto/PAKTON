"""
Description:
Routing logic for the Researcher agent workflow. Determines the next node in the graph
based on the presence of tool calls in messages, directing flow between tool execution
and response generation phases.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from Researcher.types import RetrievalState

def tools_condition(state: RetrievalState):
    messages_key = "messages"
    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
        ai_message = messages[-1]
    elif messages := getattr(state, messages_key, []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "generate_response"