"""
Description: 
    Utility functions for generating standardized API and task responses.
    Provides consistent JSON response formatting for FastAPI endpoints
    and Celery task results with structured message templates.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

from fastapi.responses import JSONResponse

def create_response(message: str, status_code: int, data: dict = None):
    """
    Utility function to generate a standardized API response.

    Args:
        message (str): The response message.
        status_code (int): The HTTP status code.
        data (dict, optional): Additional response data.

    Returns:
        JSONResponse: The formatted JSON response.
    """
    return JSONResponse(
        content={
            "message": message,
            "statusCode": status_code,
            "data": data or {} 
        },
        status_code=status_code
    )

def create_task_response(status: str, task_id: str, message: str, data=None):
    """
    Utility function to generate a standardized task response.

    Args:
        status(str): "SUCCESS" or "FAILURE"
        task_id: Celery task ID
        message(str): Task message
        data(dict, optional): Response data (optional)

    Returns: 
        JSON-formatted response
    """
    return {
        "status": status,
        "task_id": task_id,
        "message": message,
        "data": data or {}
    }