"""
Description:
Main package initialization for the Researcher agent. Handles environment variable loading 
from multiple locations and exposes the main Researcher class for RAG-based information retrieval.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env_files(override=True):
    """
    Load environment variables from multiple locations with override support.
    
    Args:
        override: If True, variables in later files override earlier ones
    
    Returns:
        bool: True if at least one .env file was found and loaded, False otherwise
    """
    # Define environment file paths in order of increasing precedence
    env_paths = [
        Path(__file__).parent.parent.parent / '.env',   
        Path(__file__).parent.parent / '.env',             
        Path(__file__).parent / '.env',                
        Path.cwd() / '.env',        
        Path.cwd() / 'researcher.env',                     
    ]
    
    # Track if any file was found
    found_env_file = False
    
    # Load each file in order, with override behavior based on parameter
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=override)
            print(f"Loaded environment from: {env_path}")
            found_env_file = True
    
    # Print error if no .env file was found
    if not found_env_file:
        print("[ERROR] No .env file found in any of the following locations:")
        for path in env_paths:
            print(f"  - {path}")
        print("Please create a .env file with the required environment variables.")
    
    return found_env_file

# Load environment files with override enabled
env_loaded = load_env_files(override=True)
if not env_loaded:
    print("[WARNING] Continuing without environment variables. Some features may not work correctly.")

from .agent import Researcher

__all__ = ["Researcher"]