"""
Validateurs pour les paramètres de génération de musique.

Ce module contient des fonctions de validation pour s'assurer
que les paramètres d'entrée sont valides avant la génération.
"""

from typing import Optional
from src.config import get_config


class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation."""
    pass


def validate_temperature(temperature: float) -> float:
    """
    Valide et normalise la température.
    
    Args:
        temperature: Température à valider
    
    Returns:
        Température validée
    
    Raises:
        ValidationError: Si la température est invalide
    """
    config = get_config()
    min_temp = config.get("generation.min_temperature", 0.3)
    max_temp = config.get("generation.max_temperature", 1.5)
    
    if not isinstance(temperature, (int, float)):
        raise ValidationError(f"La température doit être un nombre, reçu: {type(temperature)}")
    
    if temperature < min_temp or temperature > max_temp:
        raise ValidationError(
            f"La température doit être entre {min_temp} et {max_temp}, "
            f"reçu: {temperature}"
        )
    
    return float(temperature)


def validate_length(length: int) -> int:
    """
    Valide et normalise la longueur de génération.
    
    Args:
        length: Longueur à valider
    
    Returns:
        Longueur validée
    
    Raises:
        ValidationError: Si la longueur est invalide
    """
    config = get_config()
    min_length = config.get("generation.min_length", 100)
    max_length = config.get("generation.max_length", 800)
    
    if not isinstance(length, int):
        raise ValidationError(f"La longueur doit être un entier, reçu: {type(length)}")
    
    if length < min_length or length > max_length:
        raise ValidationError(
            f"La longueur doit être entre {min_length} et {max_length}, "
            f"reçu: {length}"
        )
    
    return int(length)


def validate_key(key: str) -> str:
    """
    Valide la tonalité.
    
    Args:
        key: Tonalité à valider
    
    Returns:
        Tonalité validée
    
    Raises:
        ValidationError: Si la tonalité est invalide
    """
    config = get_config()
    available_keys = config.get("generation.available_keys", [])
    
    if not isinstance(key, str):
        raise ValidationError(f"La tonalité doit être une chaîne, reçu: {type(key)}")
    
    if key not in available_keys:
        raise ValidationError(
            f"Tonalité invalide: {key}. "
            f"Tonalités disponibles: {', '.join(available_keys)}"
        )
    
    return key


def validate_meter(meter: str) -> str:
    """
    Valide la métrique.
    
    Args:
        meter: Métrique à valider
    
    Returns:
        Métrique validée
    
    Raises:
        ValidationError: Si la métrique est invalide
    """
    config = get_config()
    available_meters = config.get("generation.available_meters", [])
    
    if not isinstance(meter, str):
        raise ValidationError(f"La métrique doit être une chaîne, reçu: {type(meter)}")
    
    if meter not in available_meters:
        raise ValidationError(
            f"Métrique invalide: {meter}. "
            f"Métriques disponibles: {', '.join(available_meters)}"
        )
    
    return meter


def validate_seed_string(seed: str, char2idx: dict) -> str:
    """
    Valide la chaîne de départ (seed).
    
    Args:
        seed: Chaîne de départ à valider
        char2idx: Dictionnaire de mapping caractère -> index
    
    Returns:
        Chaîne de départ validée
    
    Raises:
        ValidationError: Si la seed est invalide
    """
    if not isinstance(seed, str):
        raise ValidationError(f"La seed doit être une chaîne, reçu: {type(seed)}")
    
    if len(seed) == 0:
        raise ValidationError("La seed ne peut pas être vide")
    
    # Vérifier que tous les caractères sont dans le vocabulaire
    invalid_chars = [c for c in seed if c not in char2idx]
    if invalid_chars:
        raise ValidationError(
            f"Caractères invalides dans la seed: {set(invalid_chars)}. "
            f"Utilisez uniquement des caractères du vocabulaire."
        )
    
    return seed
