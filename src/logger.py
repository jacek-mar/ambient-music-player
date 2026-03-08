import logging
import sys
from pathlib import Path

from .config import APP_NAME, LOG_PATH


def setup_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name or APP_NAME)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()
