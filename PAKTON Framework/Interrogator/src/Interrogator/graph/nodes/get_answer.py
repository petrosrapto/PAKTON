"""
Description:
Graph node that retrieves answers to generated questions by interfacing with the Researcher agent's document search capabilities.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from Interrogator.types import InterrogationState
from Researcher import Researcher

config = {
    "enable_hybrid": True,
    # "enable_vectordb": True,
    "run_name": "Researcher",
}

researcher = Researcher(config)

def get_answer(state: InterrogationState):
    """ Node to get an answer to a question """ 

    messages = state["messages"]
    question = messages[-1]

    if hasattr(question, "content"):  
        question = question.content  # Extract the text content

    instructions_for_search = "**SEARCH STORED DOCUMENTS** in the document database in order to answer the query."

    search_config = {"return_chunks": False}

    return {"messages": [researcher.search(query=question, instructions=instructions_for_search, config=search_config).get("response", "No response generated")]}