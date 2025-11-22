"""
Description: 
    Configuration settings for the application.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

class Config:

    @staticmethod
    def get_required_env(key: str) -> str:
        value = os.getenv(key)
        if value is None:
            raise EnvironmentError(f"Required environment variable '{key}' is not set.")
        return value

    SERVICE_NAME = get_required_env("SERVICE_NAME")
    SERVICE_QUEUE = f"{SERVICE_NAME}_queue"

    ############################# Celery Configuration #########################
    # passed from docker-compose.yml
    CELERY_BROKER_URL = get_required_env("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = get_required_env("CELERY_RESULT_BACKEND")
    TASK_ROUTES = { f"{SERVICE_NAME}.tasks.*": {"queue": SERVICE_QUEUE} }
    ############################################################################
