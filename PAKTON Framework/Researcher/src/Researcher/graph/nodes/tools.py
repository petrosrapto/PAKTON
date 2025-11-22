"""
Description:
Tool execution node for the Researcher agent that handles invocation of retrieval tools.
Processes tool calls from the graph workflow and aggregates retrieved documents from
multiple retrieval sources into the shared state.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from Researcher.types import RetrievalState

from langchain.tools import Tool    

def ToolNode(state: RetrievalState, tools: list[Tool]):
    retrievedDocuments = []
    tools_by_name = {tool.name: tool for tool in tools}
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        docs = tool.invoke(tool_call["args"])
        retrievedDocuments.extend(docs)
    return {"retrievedDocuments": retrievedDocuments}
    