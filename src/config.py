"""
Configuration centralisée pour le générateur de musique AI.

Ce module contient toutes les configurations par défaut et permet
de charger des configurations depuis des fichiers YAML/JSON.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class Config:
    """Classe de configuration centralisée."""
    
    # Chemins par défaut
    DEFAULT_MODEL_PATH = "best_model.pth"
    DEFAULT_VOCAB_PATH = "vocab.json"
    DEFAULT_OUTPUT_DIR = "outputs"
    
    # Paramètres du modèle (optimisés CPU, alignés avec le notebook)
    MODEL_CONFIG = {
        "embedding_dim": 128,
        "hidden_dim": 256,
        "num_layers": 2,
        "dropout": 0.3,
    }
    
    # Paramètres d'entraînement
    TRAINING_CONFIG = {
        "epochs": 12,
        "batch_size": 128,
        "learning_rate": 0.001,
        "seq_length": 64,
        "dataset_fraction": 0.4,
        "train_split": 0.95,
        "gradient_clip": 1.0,
        "early_stopping_patience": 3,
        "scheduler_patience": 2,
        "scheduler_factor": 0.5,
    }
    
    # Paramètres de génération
    GENERATION_CONFIG = {
        "default_temperature": 0.8,
        "min_temperature": 0.3,
        "max_temperature": 1.5,
        "default_length": 400,
        "min_length": 100,
        "max_length": 800,
        "default_key": "C",
        "default_meter": "4/4",
        "available_keys": ["C", "D", "E", "F", "G", "A", "B",
                          "Cm", "Dm", "Em", "Fm", "Gm", "Am", "Bm"],
        "available_meters": ["2/4", "3/4", "4/4", "6/8"],
    }

    # MusicGen pretrained
    AUDIO_CONFIG = {
        "model_id": "facebook/musicgen-small",
        "default_duration": 8,
        "min_duration": 5,
        "max_duration": 15,
        "device": "auto",
    }
    
    # Paramètres de l'interface
    INTERFACE_CONFIG = {
        "server_name": "0.0.0.0",
        "server_port": 7860,
        "share": False,
    }
    
    # Paramètres de logging
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "music_generator.log",
        "console": True,
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise la configuration.
        
        Args:
            config_path: Chemin vers un fichier de configuration YAML/JSON (optionnel)
        """
        self._config = {}
        self._load_defaults()
        
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
    
    def _load_defaults(self):
        """Charge les configurations par défaut."""
        self._config = {
            "model": self.MODEL_CONFIG.copy(),
            "training": self.TRAINING_CONFIG.copy(),
            "generation": self.GENERATION_CONFIG.copy(),
            "audio": self.AUDIO_CONFIG.copy(),
            "interface": self.INTERFACE_CONFIG.copy(),
            "logging": self.LOGGING_CONFIG.copy(),
            "paths": {
                "model": self.DEFAULT_MODEL_PATH,
                "vocab": self.DEFAULT_VOCAB_PATH,
                "output": self.DEFAULT_OUTPUT_DIR,
            }
        }
    
    def _load_from_file(self, config_path: str):
        """
        Charge la configuration depuis un fichier.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        path = Path(config_path)
        
        if path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml':
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
        else:
            raise ValueError(f"Format de fichier non supporté: {path.suffix}")
        
        # Fusionner avec les valeurs par défaut
        self._merge_config(self._config, file_config)
    
    def _merge_config(self, base: Dict, override: Dict):
        """
        Fusionne récursivement deux dictionnaires de configuration.
        
        Args:
            base: Configuration de base
            override: Configuration à fusionner
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration par chemin.
        
        Args:
            key_path: Chemin vers la clé (ex: "model.embedding_dim")
            default: Valeur par défaut si la clé n'existe pas
        
        Returns:
            Valeur de la configuration
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Définit une valeur de configuration.
        
        Args:
            key_path: Chemin vers la clé (ex: "model.embedding_dim")
            value: Valeur à définir
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """Retourne la configuration complète sous forme de dictionnaire."""
        return self._config.copy()
    
    def save(self, filepath: str):
        """
        Sauvegarde la configuration dans un fichier.
        
        Args:
            filepath: Chemin vers le fichier de sauvegarde
        """
        path = Path(filepath)
        
        if path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml':
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        elif path.suffix.lower() == '.json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Format de fichier non supporté: {path.suffix}")


# Instance globale de configuration
_config_instance: Optional[Config] = None


def _default_config_path() -> Optional[str]:
    """Retourne le chemin vers default_config.yaml s'il existe."""
    config_file = Path(__file__).resolve().parent.parent / "config" / "default_config.yaml"
    return str(config_file) if config_file.exists() else None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Récupère l'instance globale de configuration.
    
    Args:
        config_path: Chemin vers un fichier de configuration (optionnel)
    
    Returns:
        Instance de Config
    """
    global _config_instance
    
    if _config_instance is None:
        if config_path is None:
            config_path = _default_config_path()
        _config_instance = Config(config_path)
    
    return _config_instance
