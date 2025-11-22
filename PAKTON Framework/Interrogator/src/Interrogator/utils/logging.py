"""
Description:
Logging configuration singleton that sets up structured logging with file rotation and configurable output levels based on YAML settings.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import logging
from logging.handlers import RotatingFileHandler
from .config import config  # Import our config loader

class Logger:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        """Set up the logger based on config.yaml settings."""
        log_config = config.get("logging", {})

        log_level = getattr(logging, log_config.get("level", "INFO").upper(), logging.INFO)
        log_file = log_config.get("file", "app.log")
        log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        max_size = log_config.get("rotation", "10MB")
        retention = log_config.get("retention", "10 days")
        console_output = log_config.get("console_output", False)  

        # Convert max_size to bytes
        max_size_bytes = int(max_size.replace("MB", "")) * 1024 * 1024

        # Create a rotating file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=max_size_bytes, backupCount=int(retention.split()[0]))
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)

        self.logger = logging.getLogger("AppLogger")
        self.logger.setLevel(log_level)
        self.logger.addHandler(file_handler)

        # Add a StreamHandler to print logs to stdout if enabled
        if console_output:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        self.logger.propagate = False  # Prevent duplicate logging

    def get_logger(self):
        """Return the configured logger."""
        return self.logger

# Global logger instance to be used throughout the application
logger = Logger().get_logger()