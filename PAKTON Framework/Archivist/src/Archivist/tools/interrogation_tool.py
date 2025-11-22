"""
Description:
Tool wrapper for the Interrogator agent to be used in the Archivist's ReAct agent.
Provides async tool execution for long-running interrogation tasks.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from Interrogator import Interrogator
from Archivist.utils import logger
import asyncio
import traceback


def create_interrogation_tool(config: Optional[Dict[str, Any]] = None):
    """
    Create an async interrogation tool for LangChain ReAct agents.
    
    Args:
        config: Configuration for the Interrogator agent
        
    Returns:
        A LangChain tool that performs non-blocking interrogation
    """
    interrogator = Interrogator(config=config or {})
    logger.info("Interrogation tool initialized")
    
    @tool(response_format="content_and_artifact")
    async def interrogation(
        query: str,
        context: Optional[str] = None,
        instructions: Optional[str] = None
    ) -> tuple[str, dict]:
        """
        Conduct an in-depth interrogation on a legal query for a given user contract by iteratively asking follow-up questions.
        
        This tool uses the Interrogator agent to perform a comprehensive analysis of a query
        for a specific user contract by generating strategic follow-up questions and consolidating the answers into a
        detailed report. Use this when you are confident regarding what the user asks for and has the full context needed.
        
        Args:
            query: The main query to investigate
            context: Optional additional background context about the query
            instructions: Optional special instructions for the interrogation
            
        Returns:
            A comprehensive report with the interrogation results and a conclusion.
        """
        try:
            logger.info(f"Interrogation tool called with query: {query}")
            
            # Run synchronous interrogation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: interrogator.interrogation(
                    userQuery=query,
                    userContext=context,
                    userInstructions=instructions,
                    config={}
                )
            )
            
            # Handle errors
            if result.get("status") == "error":
                return f"Error during interrogation: {result.get('error', 'Unknown error')}"

            # Format response
            report = result.get("report", "")
            conclusion = result.get("conclusion", [])
            
            response_content = f"{conclusion}"
            
            response_artifact = {
                "report": report,
                "conclusion": conclusion
            }

            return response_content, response_artifact
            
        except Exception as e:
            error_msg = f"Failed to execute interrogation: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return error_msg
    
    return interrogation
