"""
Description:
Google model interface with custom Gemma model support that handles system message conversion and provides ChatGoogleGenerativeAI instances for the Interrogator agent.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
import re
import uuid
import json
from typing import List, Optional, Any, Dict, Union, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from Interrogator.utils import config, logger

class GemmaGoogleChatModel(ChatGoogleGenerativeAI):
    """Custom ChatGoogleGenerativeAI class that handles Gemma models properly."""
    
    def _convert_messages_for_gemma(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        Converts messages to a format compatible with Gemma models.
        For Gemma models, we need to convert SystemMessages to HumanMessages since
        Gemma doesn't support developer instructions (system messages).
        
        Args:
            messages: The original message list
            
        Returns:
            The converted message list
        """
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            return messages
        
        new_messages = []
        system_content = ""
        
        # Collect all system messages
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_content += msg.content + "\n\n"
            else:
                new_messages.append(msg)
        
        # If there are system messages, prepend them to the first human message
        # or create a new human message if none exists
        if system_content:
            if new_messages and isinstance(new_messages[0], HumanMessage):
                new_messages[0] = HumanMessage(
                    content=f"{system_content}\n\n{new_messages[0].content}"
                )
            else:
                new_messages.insert(0, HumanMessage(content=system_content))
        
        return new_messages

    def _prepare_params_for_gemma(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepares parameters for Gemma models by removing unsupported features.
        
        Args:
            params: The original parameters
            
        Returns:
            Modified parameters compatible with Gemma
        """
        # Create a copy of the params to avoid modifying the original
        gemma_params = params.copy()
        
        # Remove function/tool calling parameters as they're not supported via API
        # We'll handle them through prompt engineering instead
        if "tools" in gemma_params:
            del gemma_params["tools"]
        if "tool_choice" in gemma_params:
            del gemma_params["tool_choice"]
            
        return gemma_params
    
    def _extract_function_call_from_content(self, content: str) -> Dict[str, Any]:
        """
        Extracts function call from Gemma's response content.
        
        Args:
            content: The response content from Gemma
            
        Returns:
            Dictionary with function call details or None
        """
        # Try to parse the content as JSON directly
        content = content.strip()
        try:
            # Use regex to extract JSON object from the content
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                func_call = json.loads(json_str)
                
                if "name" in func_call and "parameters" in func_call:
                    # Convert to the format expected by LangChain
                    return {
                        "id": str(uuid.uuid4()),
                        "name": func_call["name"],
                        "args": func_call["parameters"]
                    }
            
            # If we couldn't extract via regex, try parsing the whole content
            func_call = json.loads(content)
            if "name" in func_call and "parameters" in func_call:
                return {
                    "id": str(uuid.uuid4()),
                    "name": func_call["name"],
                    "args": func_call["parameters"]
                }
                
        except (json.JSONDecodeError, AttributeError):
            logger.debug(f"Could not parse function call from content: {content}")
            
        return None
    
    def _process_gemma_function_response(self, result: ChatResult, tools: List[Dict[str, Any]]) -> ChatResult:
        """
        Processes Gemma's response to add tool_calls when function calling is used.
        
        Args:
            result: The original ChatResult
            tools: The tools that were provided to the model
            
        Returns:
            Updated ChatResult with tool_calls
        """
        if not result.generations or not tools:
            return result
            
        # Process each generation to check for function calls
        for gen_idx, generation in enumerate(result.generations):
            if not hasattr(generation.message, "content") or not generation.message.content:
                continue
                
            # Extract function call from content
            func_call = self._extract_function_call_from_content(generation.message.content)
            
            if func_call:
                # Modify the message to include tool_calls
                if isinstance(generation.message, AIMessage):
                    # Add the tool_calls attribute to the AIMessage
                    generation.message.tool_calls = [func_call]
                    
                    # Clear the content since it's now a function call
                    # generation.message.content = ""
                
                # Update the generation in the result
                result.generations[gen_idx] = generation
                
        return result
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _generate to handle Gemma models specially for function calling."""
        tools = kwargs.get("tools")
        
        # For Gemma models that need special handling
        if tools and len(tools) > 0:
            # Check if this is a tools/function call request
            logger.debug("Function/tool calling detected with Gemma model")
            
            # Convert tool definitions to Gemma function format
            functions_json = []
            for tool in tools:
                func = {
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "parameters": tool["function"]["parameters"]
                }
                functions_json.append(func)
            
            # Create special prompt for Gemma function calling
            function_prompt = """You have access to functions. If you decide to invoke any of the function(s),
you MUST put it in the format of
{"name": function name, "parameters": dictionary of argument name and its value}

You SHOULD NOT include any other text in the response if you call a function
"""
            
            # Add function definitions
            import json
            function_prompt += json.dumps(functions_json, indent=2)
            
            # Create new messages with the function calling setup
            modified_messages = messages.copy()
            
            # If first message is a system message, append the function setup
            if modified_messages and isinstance(modified_messages[0], SystemMessage):
                modified_messages[0] = SystemMessage(
                    content=f"{modified_messages[0].content}\n\n{function_prompt}"
                )
            else:
                # Add function setup as a system message at the beginning
                modified_messages.insert(0, SystemMessage(content=function_prompt))
                
            # Remove tools from kwargs to avoid API errors
            kwargs_without_tools = kwargs.copy()
            if "tools" in kwargs_without_tools:
                del kwargs_without_tools["tools"]
            if "tool_choice" in kwargs_without_tools:
                del kwargs_without_tools["tool_choice"]
                
            # Convert system messages to human messages for Gemma
            modified_messages = self._convert_messages_for_gemma(modified_messages)
            
            # Call the parent class's _generate method with modified parameters
            result = super()._generate(modified_messages, stop, run_manager, **kwargs_without_tools)
            
            # Process the response to extract function calls and add them to the result
            result = self._process_gemma_function_response(result, tools)
            
            return result
        
        # Normal processing for non-function calls or non-Gemma models
        return super()._generate(messages, stop, run_manager, **kwargs)
    
    def invoke(self, input: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        """Override invoke to handle Gemma models specially."""
        if isinstance(input, list) and all(isinstance(msg, BaseMessage) for msg in input):
            input = self._convert_messages_for_gemma(input)
        return super().invoke(input, config, **kwargs)

def get_google_llm(model_id: str, **kwargs):
    """
    Returns an instance of Google's Generative AI LLM with additional parameters.

    Requires the environment variable `GOOGLE_API_KEY` to be set.

    Args:
        model_id (str): The Google AI model name or ID to use (e.g., "gemini-2.0-flash").
        **kwargs: Additional arguments (e.g., temperature, max_tokens, safety_settings).

    Returns:
        ChatGoogleGenerativeAI: Configured instance of Google's Generative AI model.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    # Use the GemmaGoogleChatModel specifically for gemma-3-27b-it
    if model_id == "gemma-3-27b-it":
        return GemmaGoogleChatModel(
            model=model_id,
            google_api_key=api_key,
            **kwargs
        )
    
    # For all other models, use the standard ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model_id,
        google_api_key=api_key,
        **kwargs
    )