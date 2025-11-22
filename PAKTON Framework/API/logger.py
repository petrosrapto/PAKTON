"""
Description: 
    Centralized logging configuration for the API service.
    Sets up structured logging with timestamps and log levels for Docker visibility.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

import logging
import sys

LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] [%(message)s]"

# Configure logging globally
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO or ERROR if needed
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],  # Log to stdout for Docker visibility
)

# Get a logger instance
logger = logging.getLogger(__name__)
logger.info("Logging system initialized.")
