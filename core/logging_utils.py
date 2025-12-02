"""
Logging utilities for Github Heroes.
"""
import logging
import sys
from pathlib import Path
from core.config import LOGS_DIR

def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration.
    """
    log_file = LOGS_DIR / "github_heroes.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name):
    """
    Get a logger instance for a module.
    """
    return logging.getLogger(name)

