"""
Description: 
    Test client for validating API endpoints and task processing functionality.
    Provides functions for testing interrogation, research, and document indexing
    endpoints with task polling and status monitoring capabilities.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

from typing import Optional
import requests
import time

# Define the base URL of your FastAPI service
BASE_URL = "http://localhost:5001"  # Change if running on a different port

# Terminal statuses for Celery tasks
TERMINAL_STATUSES = {"SUCCESS", "FAILURE", "REVOKED", "IGNORED"}

def poll_task_status(task_id, initial_interval=20, max_retries=30, backoff_factor=1):
    """
    Polls the task status until it reaches a terminal state, using exponential backoff.

    Args:
        task_id (str): The ID of the Celery task.
        initial_interval (int): Initial time in seconds to wait before the first retry.
        max_retries (int): Maximum number of status checks before giving up.
        backoff_factor (int or float): Factor by which the interval is multiplied each retry.

    Returns:
        dict: The final response from the task status check or an error message.
    """
    current_interval = initial_interval
    url = f"{BASE_URL}/task_status/{task_id}"
    print(f"################### POLLING FOR TASK: {task_id} #####################")

    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Endpoint returned error while checking task status: {response.text}")
            return None

        data = response.json()
        status = data.get("data", {}).get("task_status")

        print(f"Attempt {attempt + 1}/{max_retries}: Task {task_id} status -> {status}")

        # Check if the task has reached a terminal state
        if status in TERMINAL_STATUSES:
            print(f"Final Task Status: {status}, Endpoint's data: {data}")
            return data
        
        # If not in terminal state, wait and then retry
        time.sleep(current_interval)
        # Multiply the interval by the backoff factor to get exponential growth
        current_interval *= backoff_factor

    # If we exit the loop, we've exhausted max_retries
    print(f"Task {task_id} polling exceeded max retries.")
    return {"error": "Task polling timed out"}

hypothesis = "All Confidential Information shall be expressly identified by the Disclosing Party."

userQuery = f"Is the following hypothesis ENTAILMENT, CONTRADICTION, or NEUTRAL according to the content of the contract: <hypothesis>{hypothesis}</hypothesis>?"
userInstructions = """
The legal researcher has access to the specific contract and can help you reach a decision. You can ask him questions regarding the contract. He doesn't know what the hypothesis is.
Give the answer in only one word:
    "ENTAILMENT" if the hypothesis is explicitly supported or logically follows from the contract.
    "CONTRADICTION" if the hypothesis directly conflicts with the contract's content.
    “NEUTRAL” if the hypothesis is not mentioned in the contract or if there is insufficient information to determine whether it is true or false.
"""

userContext = """
The answer can be one of the following:
    **ENTAILMENT**:
    - The hypothesis is logically true based on the content of the contract.
    - It is explicitly stated or can be directly inferred.

    **CONTRADICTION**:
    - The hypothesis directly conflicts with the contract's content.

    **NEUTRAL**:
    - The hypothesis is unrelated to the contract, or there is insufficient information to conclude its truth or falsehood.
"""

def interrogation():
    """
    Call the /interrogation/ endpoint
    
    Returns:
        - task_id (str): The ID of the Celery task.
    """
    print("################# Request to /interrogation/ endpoint ####################")
    url = f"{BASE_URL}/interrogation/"
    payload = {"userQuery": userQuery, "userContext": userContext, "userInstructions": userInstructions}
    response = requests.post(url, json=payload)
    print(f"Endpoint's Response: {response.json()}")
    return response.json().get("data", {}).get("task_id")

import os
import json

MIME_TYPES = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.pdf': 'application/pdf'
}

def index_document(file_path: str):
    """
    Call the /index/document/ endpoint
    
    Args:
        file_path (str): Path to the file to be indexed
    
    Returns:
        str: The ID of the Celery task
    """
    print("################# Request to /index/document/ endpoint ####################")
    url = f"{BASE_URL}/index/document/"
    
    # Get file extension and corresponding MIME type
    file_extension = os.path.splitext(file_path)[1].lower()
    mime_type = MIME_TYPES.get(file_extension, 'application/octet-stream')
    
    # Prepare metadata
    # metadata = {
    #     "title": "Test Document",
    #     "author": "Test Author",
    #     "date": "2025-02-16",
    #     "iteration_id": "12",
    #     "tags": ["test", "document"]
    # }

    metadata = {"title": "Test Document","author": "Test Author"}
    
    # Open and send the file
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        data = {"metadata": json.dumps(metadata)}
        response = requests.post(url, files=files, data=data)

    print(f"Endpoint's Response: {response.json()}")
    return response.json().get("data", {}).get("task_id")

def research():
    """
    Call the /research/ endpoint
    
    Returns:
        - task_id (str): The ID of the Celery task.
    """
    print("################# Request to /research/ endpoint ####################")
    url = f"{BASE_URL}/research/"
    
    # Example hypothesis similar to what was used in the testing notebook
    hypothesis = "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement."
    query = f"Is the following hypothesis ENTAILMENT, CONTRADICTION, or NEUTRAL according to the content of the contract: <hypothesis>{hypothesis}</hypothesis>?"
    
    # Define configurations
    agent_config = {
        "enable_hybrid": True,
        "run_name": "API Research Test"
    }
    
    search_config = {
        "return_chunks": True
    }
    
    payload = {
        "query": query,
        "instructions": "Search stored documents in the document database in order to answer the query",
        "agent_config": agent_config,
        "search_config": search_config
    }
    
    response = requests.post(url, json=payload)
    print(f"Endpoint's Response: {response.json()}")
    return response.json().get("data", {}).get("task_id")

def process_query(query: str, thread_id: Optional[str] = None) -> Optional[str]:
    """
    Call the /query/celery endpoint to process a query.
    
    Args:
        query (str): The user query to process
        thread_id (Optional[str]): Optional thread ID for conversation continuity
    
    Returns:
        str: The task ID of the Celery task, or None if request failed.
    """
    print("################# Request to /query/ endpoint ####################")
    url = f"{BASE_URL}/query/celery"
    payload = {"query": query, "thread_id": thread_id}
    response = requests.post(url, json=payload)
    print(f"Endpoint's Response: {response.json()}")
    return response.json().get("data", {}).get("task_id")

def check_health() -> bool:
    """
    Call the /health endpoint to check if the service is healthy.
    
    Returns:
        bool: True if service is healthy, False otherwise.
    """
    print("################# Request to /health endpoint ####################")
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Endpoint's Response: {response.json()}")
        
        return response.status_code == 200 and response.json().get("status") == "healthy"
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return False

def check_root() -> bool:
    """
    Call the root endpoint (/) to get service information.
    
    Returns:
        bool: True if endpoint responds correctly, False otherwise.
    """
    print("################# Request to / (root) endpoint ####################")
    url = f"{BASE_URL}/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Endpoint's Response: {response.json()}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return False

if __name__ == "__main__":
    # poll_task_status(index_document("example_0.docx"))
    # poll_task_status(interrogation()) 

    # Test the research endpoint
    # First, index a document
    # file_path = "EU_AI_ACT.pdf"
    # task_id = index_document(file_path)
    # response = poll_task_status(task_id)
    # task_status = response.get("data", {}).get("task_status")
    # task_response = response.get("data", {}).get("task_response")
    # if task_status != "SUCCESS" or task_response.get("status") != "SUCCESS":  
    #     raise Exception(f"Not successful task status: {task_status}")
    
    # Then, run a research query
    # print("Research Result:", poll_task_status(research()))
    poll_task_status(process_query("Ok, what can you do for me? Give me an overview.", "12")) 