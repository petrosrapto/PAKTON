"""
Description:
Configuration management singleton for the Researcher agent. Handles loading and 
accessing configuration settings from YAML files with support for different execution
environments (development, installed package, etc.).

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import yaml
import os
from pathlib import Path
import pkg_resources  # Import to locate installed package data

class Config:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from config.yaml, handling different execution environments."""
        # Define config file paths in order of precedence
        config_paths = [
            Path.cwd() / "config.researcher.yaml",           # CWD alternative naming
            Path(__file__).parent.parent / "config.yaml",      # Researcher/src/Researcher/config.yaml
            Path("/app/Researcher/src/Researcher/config.yaml"),  # Docker mount location
            Path("/app/API/config.researcher.yaml"),         # API directory with specific name
        ]
        
        # Try pkg_resources first (for installed packages)
        try:
            pkg_config_path = pkg_resources.resource_filename("Researcher", "config.yaml")
            if os.path.exists(pkg_config_path):
                config_paths.insert(0, Path(pkg_config_path))
        except Exception:
            pass
        
        # Try each path until we find one that exists
        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            print("[ERROR] config.yaml not found in any of the following locations:")
            for path in config_paths:
                print(f"  - {path}")
            print("Please ensure config.yaml exists in one of these locations.")
            self.config = {}
            return
        
        try:
            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)
            print(f"[INFO] Successfully loaded config from {config_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load config from {config_path}: {e}")
            self.config = {}

    def get(self, key, default=None):
        """Retrieve nested configuration values using dot notation."""
        keys = key.split(".")
        current = self.config

        for k in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(k, {})

        return current if current else default

# Global instance
config = Config()
print("[DEBUG] Full config:", config.config)