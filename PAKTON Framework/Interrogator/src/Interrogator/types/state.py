"""
Description:
State definition for the Interrogator agent that maintains conversation context, user queries, interrogation progress, and configuration settings throughout the workflow.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import TypedDict, List, Dict, Any, Optional
from typing import Annotated
import operator
from langchain_core.documents import Document
from langgraph.graph import MessagesState

class InterrogationState(MessagesState):
    """
        State type for the Interrogation agent.
    """
    userQuery: str # The question the user wants to be answered
    userContext: Optional[str] # Additional context provided by the user
    userInstructions: Optional[str] # Additional instructions of the user to the interrogator
    max_num_turns: int # Number turns of interrogation

    interrogation: str # saved interrogation
    report: str # Report of the interrogation
    conclusion: str # Conclusion of the interrogation

    config: Optional[Dict[str, Any]]
