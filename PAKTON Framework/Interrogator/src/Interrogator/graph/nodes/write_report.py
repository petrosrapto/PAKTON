"""
Description:
Graph node that generates the final legal conclusion and report based on the collected interrogation data and question-answer pairs.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from Interrogator.types import InterrogationState

from Interrogator.utils import LEGAL_CONCLUSION_WRITER_PROMPT, LEGAL_CONCLUSION_USER_PROMPT

from Interrogator.models import get_default_llm

from langchain_core.messages import SystemMessage, HumanMessage

def write_report(state: InterrogationState):

    """ Node to answer a question """

    # Get state
    interrogation = state["interrogation"]
    userQuery = state["userQuery"]
    userContext = state["userContext"]
    report = state["report"]
    interrogation_summary = state["messages"][-1].content
    conclusion = get_default_llm(node_name="write_conclusion").invoke([SystemMessage(content=LEGAL_CONCLUSION_WRITER_PROMPT)]+[HumanMessage(content=LEGAL_CONCLUSION_USER_PROMPT.format(userQuery=userQuery, userContext=userContext, report=report, interrogation_summary=interrogation_summary))])             

    return {"conclusion": conclusion.content}