"""
Description:
Response generation node for the Researcher agent that synthesizes final answers from
retrieved documents. Handles document formatting, prompt construction, and LLM-based
response generation with support for structured output and content sanitization.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic.v1 import BaseModel, Field  # Updated to use pydantic.v1 for compatibility

from Researcher.types import RetrievalState
from Researcher.models import get_default_llm
from Researcher.utils import RAG_SYSTEM_PROMPT, RAG_HUMAN_PROMPT

from Researcher.utils import format_documents, sanitize_with_bleach, extract_texts_from_json

from Researcher.utils import logger, config  # Import the logger
import json5  
import json
import re
from jsonschema import validate, ValidationError

llm_filtering_config = config.get("llm_filtering", {})
use_llm_filtering = llm_filtering_config.get("use_llm_filtering", False)
model_llm_filtering = llm_filtering_config.get("model", "gpt-4o")
top_k_llm_filtering = llm_filtering_config.get("top_k", 10)

if model_llm_filtering == 'command-r':
    import cohere
    import os
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION_NAME")

    co = cohere.BedrockClient(
        aws_region=region,
        aws_access_key=aws_access_key_id,
        aws_secret_key=aws_secret_access_key
    )

class FilteredChunks(BaseModel):
    """Schema for filtering chunks."""
    relevant_chunks: List[str] = Field(
        description="List of the most relevant chunks of information that directly answer the query."
    )

def generate_response(state: RetrievalState) -> Dict[str, Any]:
    """Generate a response based on the retrieved documents.
    
    Args:
        state: Current state of the agent with retrievedDocuments
        
    Returns:
        Updated state with the generated response
    """
    # Get state components
    query = state.get("query", "")
    documents = state.get("responseContext", [])
    # documents = state.get("retrievedDocuments", [])
    
    # Check if return_chunks is enabled
    return_chunks = state.get("config", {}).get("return_chunks", False)

    # Format the documents for the LLM

    context_text = format_documents(documents)
    
    # Get the LLM with node-specific configuration
    llm = get_default_llm(node_name="response_generator")
    
    if return_chunks:
        if not documents:
            response_content = f"For the query '{query}', the are not any relevant spans from the original documents."
            logger.info("No relevant spans found.")
            return {"response": response_content}
        
        if use_llm_filtering:
            logger.info("Return chunks mode enabled, filtering chunks...")

            if model_llm_filtering == 'gpt-4o':
                context_text = format_documents(documents[:10]) # top 10 chunks only for testing
                system_message = SystemMessage(content=(f"""
                You are a highly accurate document filtering system.

                Your task is to review the provided retrieved context (given as chunks) and select **only the specific spans** that are directly answer the query.

                - Do **not** modify the content of any chunk other than isolating some spans.
                - Do **not** provide commentary, summaries, or explanations.
                - If only a portion (span) of a chunk is relevant, extract **only that span**.
                - If **multiple non-contiguous spans** within the same chunk are relevant, treat **each span as a separate chunk** in your output.
                - Output the spans in descending order of relevance to the query. The most relevant span should be first.
                - A span is defined as a contiguous sequence of characters within a chunk. If **multiple non-contiguous sequences** within the same chunk are relevant, treat **each sequence as a separate span** in your output.
                - If a sequence is contiguous, treat it as a single span and do not split it in your output.
                                                                            
                Return only the exact text of the relevant spans — nothing else.

                Focus on **precision**. Your goal is to isolate the minimal amount of text needed to fully support an accurate answer.
                """))
                
                # Create the human message with context and query
                human_message = HumanMessage(content=(
                    f"Query: {query}\n\n"
                    f"Retrieved Context:\n{context_text}\n\n"
                    "Return the most relevant spans in JSON format."
                    "Each span should directly help answer the query."
                    "You can isolate spans of text from the chunks if necessary but do not modify the content."
                ))
                
                # Generate filtered chunks with structured output
                filtered_chunks_response = llm.with_structured_output(FilteredChunks).invoke(
                    [system_message, human_message]
                )
                
                # Concatenate the filtered chunks
                chunks = filtered_chunks_response.relevant_chunks

            elif model_llm_filtering == 'command-r':

                ### MAYBE I SHOULD ISOLATE ONLY THE ORIGINAL SPANS?

                retrievedDocuments = documents[:10]  
                documents = []
                for doc in retrievedDocuments:
                    documents.append({"data": doc.page_content})

                # message=f"I provided you some documents. Give me the exact spans that answer the question: '{query}'"

                message = f"""
                You are a highly accurate document filtering system.

                Your task is to review the provided documents and select **only the specific spans** from the documents that directly answer the query.
                Focus on **precision**, don't provide general information. 

                Query: {query}\n\n

                - Do **not** modify the content of any individual document other than isolating some spans.
                - If only a portion (span) is relevant, extract **only that span**.
                - If a whole document is irrelevant, do not include it in your output.
                - A span is defined as a contiguous sequence of characters within a document. If **multiple non-contiguous sequences** within the same document are relevant, treat **each sequence as a separate span** in your output.
                - If a contiguous sequence is relevant, treat it as a single span and do not split it in your output.
                - Isolate the minimal amount of text needed as spans to answer the query.

                Give the answer in valid JSON format with the following structure:
                ```
                {{{{
                    "spans": [
                        {{"text": "string"}}
                    ]
                }}}}
                ```
                """

                response_format = {
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "spans": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"}
                                    },
                                    "required": ["text"],
                                },
                            }
                        },
                        "required": ["spans"],
                    },
                }

                # Add retry mechanism for JSON validation
                max_retries = 5
                retry_count = 0
                chunks = []

                while retry_count < max_retries:
                    try:
                        response = co.chat(
                            model="cohere.command-r-v1:0",
                            message=message,
                            documents=documents
                        )
                        
                        logger.info(f"Attempt {retry_count + 1}: Received response from Cohere: {response.text}")
                        
                        # Try to parse the JSON response
                        try:
                            match = re.search(r"```json\s*(.*?)```", response.text, re.DOTALL)
                            if match:
                                json_str = match.group(1).strip()
                            else:
                                json_str = response.text
                            logger.info(f"Extracted JSON string: {repr(json_str)}")
                            
                            if retry_count != 0:
                                # strip xml and html tags
                                json_str = sanitize_with_bleach(json_str)

                            # json5 is a more relaxed JSON parser that can handle trailing commas and comments
                            if retry_count != 0:
                                response_data = extract_texts_from_json(json_str.replace('\xa0', ' '))
                            else:
                                response_data = json5.loads(json_str.replace('\xa0', ' '))
                            # validate(instance=response_data, schema=response_format["schema"])
                            # logger.info("Valid JSON response received")
                            
                            # Extract spans from the valid JSON
                            chunks = [span["text"] for span in response_data["spans"]]
                            break  # Exit the loop if successful
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.warning(f"Invalid JSON response on attempt {retry_count + 1}: {e}")
                            retry_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error calling Cohere API: {e}")
                        retry_count += 1
            
            if chunks:
                response_content = "\n---\n" + "\n---\n".join(chunks[:top_k_llm_filtering]) + "\n---\n"
            else:
                response_content = ""
            
            logger.info("Filtered chunks: %s", response_content)

            response_content = f"For the query '{query}', the most relevant spans from the original documents are:\n\n{response_content}"
            
            return {"response": response_content}

    else:
        # Standard response generation (existing flow)
        # Create the messages for response generation
        system_message = SystemMessage(content=RAG_SYSTEM_PROMPT)
        
        # Put the context and query in the human message
        human_prompt_template = PromptTemplate.from_template(RAG_HUMAN_PROMPT)
        human_message_content = human_prompt_template.format(
            context=context_text,
            query=query if query else "Please provide information based on the retrieved data."
        )
        
        human_message = HumanMessage(content=human_message_content)
        
        # Generate response
        input_messages = [system_message, human_message]
        response = llm.invoke(input_messages)
        
        logger.info("Generated response: %s", response.content)

        return {"response": response.content}