"""
Utilitaires pour parser et manipuler la notation ABC.

Ce module contient des fonctions pour extraire et nettoyer
la notation ABC depuis différents formats.
"""

import re
from typing import Optional


def extract_abc_notation(text: str) -> str:
    """
    Extrait la notation ABC pure du texte.
    
    Nettoie le texte en retirant les préfixes comme "Assistant: "
    et les balises de fin comme "</s>".
    
    Args:
        text: Texte brut contenant potentiellement de la notation ABC
    
    Returns:
        Notation ABC nettoyée
    """
    # Retirer le préfixe "Assistant: " si présent
    if 'Assistant:' in text:
        text = text.split('Assistant:', 1)[1].strip()
    
    # Retirer les balises </s>
    text = text.replace('</s>', '').strip()
    
    # Retirer les espaces en début et fin
    text = text.strip()
    
    return text


def parse_abc(abc_text: str) -> dict:
    """
    Parse une notation ABC et extrait les métadonnées.
    
    Args:
        abc_text: Notation ABC à parser
    
    Returns:
        Dictionnaire contenant les métadonnées extraites:
        - title: Titre de la pièce
        - key: Tonalité
        - meter: Métrique
        - length: Longueur de note par défaut
        - body: Corps de la notation (les notes)
    """
    metadata = {
        'title': None,
        'key': None,
        'meter': None,
        'length': None,
        'body': abc_text
    }
    
    lines = abc_text.split('\n')
    body_start = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Parser les champs ABC
        if line.startswith('X:'):
            # Numéro de référence (ignoré pour l'instant)
            body_start = i + 1
        elif line.startswith('T:'):
            # Titre
            metadata['title'] = line[2:].strip()
            body_start = i + 1
        elif line.startswith('K:'):
            # Tonalité
            metadata['key'] = line[2:].strip()
            body_start = i + 1
        elif line.startswith('M:'):
            # Métrique
            metadata['meter'] = line[2:].strip()
            body_start = i + 1
        elif line.startswith('L:'):
            # Longueur de note par défaut
            metadata['length'] = line[2:].strip()
            body_start = i + 1
        elif line and not line.startswith('%'):
            # Ligne de notes (pas un commentaire)
            body_start = i
            break
    
    # Extraire le corps (les notes)
    metadata['body'] = '\n'.join(lines[body_start:])
    
    return metadata


def is_valid_abc(abc_text: str) -> bool:
    """
    Vérifie si une chaîne est une notation ABC valide.
    
    Args:
        abc_text: Texte à vérifier
    
    Returns:
        True si le texte semble être une notation ABC valide
    """
    if not abc_text or len(abc_text.strip()) == 0:
        return False
    
    # Vérifier la présence de champs ABC de base
    has_reference = 'X:' in abc_text
    has_key = 'K:' in abc_text
    
    # Une notation ABC valide doit au moins avoir une référence et une tonalité
    return has_reference and has_key
