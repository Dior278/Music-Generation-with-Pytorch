"""
Configuration du système de logging.

Ce module configure le système de logging pour l'application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from src.config import get_config


def setup_logging(config_path: Optional[str] = None) -> logging.Logger:
    """
    Configure le système de logging.
    
    Args:
        config_path: Chemin vers un fichier de configuration (optionnel)
    
    Returns:
        Logger configuré
    """
    config = get_config(config_path)
    logging_config = config.get("logging", {})
    
    # Niveau de logging
    level = getattr(logging, logging_config.get("level", "INFO").upper())
    
    # Format
    log_format = logging_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Formatter
    formatter = logging.Formatter(log_format)
    
    # Logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Retirer les handlers existants
    root_logger.handlers.clear()
    
    # Handler console
    if logging_config.get("console", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Handler fichier
    log_file = logging_config.get("file")
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


# Configuration automatique au chargement du module
setup_logging()
