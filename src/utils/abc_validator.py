"""
ABC notation validator and cleaner for MIDI compatibility.

This module cleans and validates ABC notation to prevent errors
during MIDI conversion.
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def clean_abc_for_midi(abc_text: str) -> str:
    """
    Nettoie la notation ABC pour garantir une conversion MIDI réussie.
    Supprime les en-têtes dupliqués et garantit un format valide.
    
    Args:
        abc_text: Notation ABC à nettoyer
    
    Returns:
        Notation ABC nettoyée et validée
    """
    lines = abc_text.split('\n')
    cleaned_lines = []
    
    # État pour suivre les sections et éviter les doublons
    has_x = False
    has_k = False
    has_m = False
    has_l = False
    has_t = False
    in_body = False
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Ignorer les lignes vides
        if not line:
            if in_body:
                cleaned_lines.append('')
            continue
        
        # Ignorer les commentaires
        if line.startswith('%'):
            continue
        
        # Traiter les en-têtes (un seul de chaque type)
        if line.startswith('X:'):
            if not has_x:  # Éviter les doublons
                has_x = True
                # S'assurer que X: a une valeur
                if len(line) == 2:
                    line = 'X:1'
                cleaned_lines.append(line)
            continue
        
        if line.startswith('T:'):
            if not has_t:  # Éviter les doublons
                has_t = True
                cleaned_lines.append(line)
            continue
        
        if line.startswith('M:'):
            if not has_m:  # Éviter les doublons de métrique
                has_m = True
                # Valider le format de métrique
                meter = line[2:].strip()
                if not re.match(r'^\d+/\d+$', meter):
                    line = 'M:4/4'  # Par défaut
                cleaned_lines.append(line)
            continue
        
        if line.startswith('L:'):
            if not has_l:  # Éviter les doublons
                has_l = True
                # Valider le format de longueur
                length = line[2:].strip()
                if not re.match(r'^\d+/\d+$', length):
                    line = 'L:1/8'  # Par défaut
                cleaned_lines.append(line)
            continue
        
        if line.startswith('K:'):
            if not has_k:  # Éviter les doublons de tonalité
                has_k = True
                in_body = True
                # Nettoyer la tonalité
                key = line[2:].strip()
                # Garder seulement la partie principale (C, D, Am, etc.)
                key = re.sub(r'[^A-Ga-gm]', '', key)
                if not key:
                    key = 'C'
                line = f'K:{key}'
                cleaned_lines.append(line)
            continue
        
        # Ignorer les autres en-têtes dans le corps (Q:, R:, C:, etc.)
        if in_body and line.startswith(('Q:', 'R:', 'C:', 'M:', 'L:', 'K:')):
            # Ces en-têtes ne doivent pas apparaître dans le corps
            continue
        
        # Traiter le corps (notes)
        if in_body or (line and not line.startswith(('Q:', 'R:', 'C:', 'M:', 'L:', 'K:'))):
            # Nettoyer la ligne de notes
            cleaned_line = clean_music_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
    
    # S'assurer que les en-têtes requis sont présents (une seule fois)
    if not has_x:
        cleaned_lines.insert(0, 'X:1')
    
    if not has_k:
        # Ajouter K: à la fin des en-têtes
        for i, line in enumerate(cleaned_lines):
            if line.startswith('L:') or line.startswith('M:'):
                cleaned_lines.insert(i + 1, 'K:C')
                break
        else:
            cleaned_lines.insert(0, 'K:C')
    
    if not has_m:
        # Ajouter M:4/4 par défaut (une seule fois)
        for i, line in enumerate(cleaned_lines):
            if line.startswith('X:'):
                cleaned_lines.insert(i + 1, 'M:4/4')
                break
    
    if not has_l:
        # Ajouter L:1/8 par défaut (une seule fois)
        for i, line in enumerate(cleaned_lines):
            if line.startswith('M:'):
                cleaned_lines.insert(i + 1, 'L:1/8')
                break
    
    return '\n'.join(cleaned_lines)


def clean_music_line(line: str) -> str:
    """
    Nettoie une ligne de notation musicale ABC.
    
    Args:
        line: Ligne de notes ABC
    
    Returns:
        Ligne nettoyée
    """
    # Retirer les caractères invalides
    # Garder: lettres (notes), chiffres (durées), / (fractions), 
    # espaces, | (barres), " (accords), - (liaisons), 
    # ' (octaves), , (octaves), ( ) (groupes)
    
    # Pattern pour garder les caractères valides ABC
    valid_chars = r'[A-Ga-g0-9/\s|"\'\-,\[\](){}#b=~.xyzXYZ]'
    
    # Extraire les parties valides
    cleaned = ''
    i = 0
    while i < len(line):
        char = line[i]
        
        # Gérer les accords (entre guillemets)
        if char == '"':
            cleaned += char
            i += 1
            # Trouver la fin de l'accord
            while i < len(line) and line[i] != '"':
                if line[i].isalnum() or line[i] in ['#', 'b', 'm', '7', '9']:
                    cleaned += line[i]
                i += 1
            if i < len(line):
                cleaned += line[i]  # Fermer les guillemets
                i += 1
            continue
        
        # Vérifier si le caractère est valide
        if re.match(valid_chars, char):
            cleaned += char
        i += 1
    
    # Nettoyer les espaces multiples
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


def validate_abc_for_midi(abc_text: str) -> tuple[bool, Optional[str]]:
    """
    Valide la notation ABC pour la conversion MIDI.
    
    Args:
        abc_text: Notation ABC à valider
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not abc_text or not abc_text.strip():
        return False, "Notation ABC vide"
    
    # Vérifier les en-têtes requis
    if 'X:' not in abc_text:
        return False, "En-tête X: manquant"
    
    if 'K:' not in abc_text:
        return False, "En-tête K: (tonalité) manquant"
    
    # Vérifier qu'il y a du contenu musical
    lines = abc_text.split('\n')
    has_music = False
    for line in lines:
        line = line.strip()
        if line and not line.startswith(('X:', 'T:', 'M:', 'L:', 'K:', 'Q:', 'R:', 'C:', '%')):
            # Ligne de musique
            if re.search(r'[A-Ga-g]', line):
                has_music = True
                break
    
    if not has_music:
        return False, "Aucune note musicale trouvée"
    
    return True, None
