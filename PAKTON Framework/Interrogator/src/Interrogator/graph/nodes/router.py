"""
Description:
Routing logic for determining whether the interrogation process should continue based on turn limits and confidence indicators from the interrogator.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import Dict, Any

from Interrogator.types import InterrogationState

from Interrogator.models import similarity_check

def route_interrogation(state: InterrogationState) -> str:
    """Router to determine if the interview will continue.
    
    Args:
        state: Current state of the agent
        
    Returns:
        The next state to transition to
    """
    
    # Get messages
    messages = state["messages"]
    max_num_turns = state.get('max_num_turns')

    # End if expert has answered more than the max turns
    if (len(messages) // 2) >= max_num_turns:
        return 'save_interrogation'
    
    last_question = messages[-1]
    # if 'Thank you, I am now in a position to answer the question with confidence.' in last_question.content:
    #     return 'save_interrogation'
    if 'Thank you, I am now in a position to answer the question with confidence.' in last_question.content or similarity_check(last_question.content, 'Thank you, I am now in a position to answer the question with confidence.'):
        return 'save_interrogation'
    return 'get_answer'
