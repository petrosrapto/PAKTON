"""
Description:
Graph node that generates strategic legal questions for the interrogation process, adapting prompts based on conversation state and remaining question turns.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from Interrogator.types import InterrogationState
from Interrogator.utils import INTERROGATION_SYSTEM_PROMPT, INTERROGATION_SYSTEM_PROMPT_FIRST_QUESTION, INTERROGATION_USER_PROMPT, INTERROGATION_USER_PROMPT_FIRST_QUESTION, INTERROGATION_SYSTEM_PROMPT_FINAL_QUESTION, INTERROGATION_USER_PROMPT_FINAL_QUESTION
from Interrogator.models import get_default_llm

from langchain_core.prompts import PromptTemplate

def generate_question(state: InterrogationState):
    """ Node to generate a question """

    messages = state["messages"]
    userQuery = state["userQuery"]
    userContext = state["userContext"]
    userInstructions = state["userInstructions"]
    remaining_questions = int(state["max_num_turns"] - len(messages) / 2)

    # Check if the report already exists (if it doesnt exist, this is the first question)
    # If it does, we need to format the system prompt differently
    node_name = "question_generator"
    if "report" in state and state["report"]:

        if remaining_questions == 0:
                        
            # Format the system prompt
            system_prompt = INTERROGATION_SYSTEM_PROMPT_FINAL_QUESTION.format(
                userQuery=userQuery,
                remaining_questions=remaining_questions,
                userContext=userContext,
                userInstructions=userInstructions
            )

            questions_text = "\n".join(msg.content for msg in messages[::2])

            user_prompt = INTERROGATION_USER_PROMPT_FINAL_QUESTION.format(
                report=state["report"],
                questions=questions_text
            )

            node_name = "write_conclusion"

        else:

            # Format the system prompt
            system_prompt = INTERROGATION_SYSTEM_PROMPT.format(
                userQuery=userQuery,
                remaining_questions=remaining_questions,
                userContext=userContext,
                userInstructions=userInstructions
            )

            questions_text = "\n".join(msg.content for msg in messages[::2])

            user_prompt = INTERROGATION_USER_PROMPT.format(
                report=state["report"],
                questions=questions_text
            )
    
    else:
                # Format the system prompt
        system_prompt = INTERROGATION_SYSTEM_PROMPT_FIRST_QUESTION.format(
            userQuery=userQuery,
            remaining_questions=remaining_questions,
            userContext=userContext,
            userInstructions=userInstructions
        )

        user_prompt = INTERROGATION_USER_PROMPT_FIRST_QUESTION.format(
            userQuery=userQuery,
            userContext=userContext,
            userInstructions=userInstructions
        )

    # Invoke the LLM with the system message and formatted conversation
    question = get_default_llm(node_name=node_name).invoke([SystemMessage(content=system_prompt)]+[HumanMessage(content=user_prompt)])
    
    # Write messages to state
    return {"messages": [question]}