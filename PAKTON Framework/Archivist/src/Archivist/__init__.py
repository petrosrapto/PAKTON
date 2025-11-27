"""
Description:
Archivist package initialization module. Loads environment variables from multiple locations
with override support and initializes the main Archivist agent class.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import pkg_resources

def load_env_files():
    """
    Load environment variables from the first matching .env file found.
    Checks pkg_resources first, then searches through predefined paths.
    Only the first matching file is loaded (no merging or override).
    
    Returns:
        bool: True if a .env file was found and loaded, False otherwise
    """
    # Define environment file paths in order of precedence
    env_paths = [
        Path.cwd() / 'archivist.env',
        Path.cwd() / '.env',
        Path(__file__).parent / '.env',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent.parent / '.env',
    ]
    
    # Try pkg_resources first (for installed packages)
    try:
        pkg_env_path = pkg_resources.resource_filename("Archivist", ".env")
        if os.path.exists(pkg_env_path):
            env_paths.insert(0, Path(pkg_env_path))
    except Exception:
        pass
    
    # Try each path until we find one that exists
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=True)
            print(f"[INFO] Loaded environment from: {env_path}")
            return True
    
    # Print error if no .env file was found
    print("[ERROR] No .env file found in any of the following locations:")
    for path in env_paths:
        print(f"  - {path}")
    print("Please create a .env file with the required environment variables.")
    return False

# Load environment file (first match only)
env_loaded = load_env_files()
if not env_loaded:
    print("[WARNING] Continuing without environment variables. Some features may not work correctly.")

from .agent import Archivist

__all__ = ["Archivist"]