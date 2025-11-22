"""
Description:
Configuration management singleton class. Loads and provides access to YAML configuration
with support for nested key retrieval using dot notation.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import yaml
import os
from pathlib import Path
import pkg_resources  # Import to locate installed package data

def get_required_env(key):
    value = os.getenv(key)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value

def get_required_config(key, config):
    value = config.get(key, None)
    if value is None:
        raise EnvironmentError(f"Required config variable '{key}' is not set.")
    return value

class Config:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from config.yaml, handling different execution environments."""
        try:

            try:
                config_path = pkg_resources.resource_filename("Archivist", "config.yaml")
                if not os.path.exists(config_path):
                    raise FileNotFoundError
            except Exception:
                config_path = None  # If not found in package, try another method
            
            if config_path is None:
                project_root = Path(__file__).resolve().parents[3]  # Adjust based on depth
                config_path = project_root / "config.yaml"
                
                if not config_path.exists():
                    raise FileNotFoundError(f"[ERROR] config.yaml not found at: {config_path}")

            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)

            print(f"[INFO] Successfully loaded config from {config_path}")

        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
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
    
    def get_required(self, key):
        value = self.get(key, None)
        if value is None:
            raise EnvironmentError(f"Required config variable '{key}' is not set.")
        return value

# Global instance
config = Config()
print("[DEBUG] Full config:", config.config)