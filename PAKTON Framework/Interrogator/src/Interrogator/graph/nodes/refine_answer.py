"""
Description:
Graph node that refines and consolidates answers from the research process, creating or updating comprehensive reports based on conversation history.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from Interrogator.types import InterrogationState

from Interrogator.utils import LEGAL_REPORT_WRITER_PROMPT, LEGAL_REPORT_USER_PROMPT, ANSWER_REFINING_PROMPT, ANSWER_REFINING_USER_PROMPT, format_conversation

from Interrogator.models import get_default_llm

from langchain_core.messages import SystemMessage, HumanMessage

def refine_answer(state: InterrogationState):

    """ Node to answer a question """

    # Get state
    messages = state["messages"]
    userQuery = state["userQuery"]
    userContext = state["userContext"]

    # Check if the report already exists
    if "report" in state and state["report"]:
        # report exists, refine it
        # pass as the conversation the latest question and answer
        conversation = format_conversation(messages[-2:], "Legal Interrogator", "Legal Researcher")
        refined_answer = get_default_llm(node_name="report_generator").invoke([SystemMessage(content=ANSWER_REFINING_PROMPT)]+[HumanMessage(content=ANSWER_REFINING_USER_PROMPT.format(userQuery=userQuery, userContext=userContext, conversation=conversation, existingReport=state["report"]))]) 
        return {"report": refined_answer.content}
    interrogation = format_conversation(messages, "Legal Interrogator", "Legal Researcher")
    report = get_default_llm(node_name="report_generator").invoke([SystemMessage(content=LEGAL_REPORT_WRITER_PROMPT)]+[HumanMessage(content=LEGAL_REPORT_USER_PROMPT.format(userQuery=userQuery, userContext=userContext, conversation=interrogation))]) 
    return {"report": report.content}

