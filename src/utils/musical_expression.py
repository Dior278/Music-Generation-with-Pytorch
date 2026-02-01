"""
Musical expression module for enriching ABC notation.

This module adds sensitivity, dynamics, chords, and variety
throughout the music, not just at the beginning.
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def enrich_music_line_with_expression(line: str, 
                                     chord: str,
                                     position: int,
                                     add_chords_midline: bool = True,
                                     add_dynamics_midline: bool = True,
                                     add_articulations: bool = True) -> str:
    """
    Enrichit une ligne de musique avec des accords, nuances et articulations
    tout au long de la ligne, pas seulement au début.
    
    Args:
        line: Ligne de notation ABC
        chord: Accord à utiliser
        position: Position dans la pièce
        add_chords_midline: Si True, ajoute des accords au milieu de la ligne
        add_dynamics_midline: Si True, ajoute des nuances au milieu
        add_articulations: Si True, ajoute des articulations (staccato, legato)
    
    Returns:
        Ligne enrichie avec expression musicale
    """
    if not line.strip() or not chord:
        return line
    
    # Extraire les notes de la ligne (sans les accords existants)
    # Pattern pour trouver les notes: lettres A-G avec optionnel #, b, chiffres
    notes_pattern = r'([A-Ga-g][#b]?[0-9]*[/0-9]*)'
    notes = re.findall(notes_pattern, line)
    
    if not notes:
        return line
    
    # Diviser la ligne en segments pour ajouter des accords et nuances au milieu
    result_parts = []
    notes_per_segment = max(2, len(notes) // 3)  # 3 segments par ligne environ
    
    i = 0
    segment_num = 0
    
    # Traiter la ligne caractère par caractère pour préserver le format
    current_segment = ""
    notes_in_segment = 0
    
    j = 0
    while j < len(line):
        char = line[j]
        current_segment += char
        
        # Détecter une note
        if re.match(r'[A-Ga-g]', char):
            notes_in_segment += 1
            
            # Ajouter un accord au milieu si on a assez de notes
            if add_chords_midline and notes_in_segment > 0 and notes_in_segment % notes_per_segment == 0:
                # Ajouter l'accord avant cette note
                if segment_num > 0:  # Pas au tout début
                    result_parts.append(f'"{chord}" ')
                segment_num += 1
            
            # Ajouter une nuance dynamique au milieu
            if add_dynamics_midline and notes_in_segment % (notes_per_segment + 1) == 0:
                dynamics = ['p', 'mf', 'f', 'mp', 'cresc', 'dim']
                dynamic = dynamics[(position + segment_num) % len(dynamics)]
                result_parts.append(f'!{dynamic}! ')
        
        j += 1
    
    # Si on n'a rien ajouté, ajouter au moins au début
    if not result_parts and add_chords_midline:
        result_parts.append(f'"{chord}" ')
    
    return ''.join(result_parts) + line


def add_chords_throughout_line(line: str, chord: str, notes: List[str]) -> str:
    """
    Ajoute des accords tout au long d'une ligne de musique.
    
    Args:
        line: Ligne de notation ABC
        chord: Accord à ajouter
        notes: Liste des notes dans la ligne
    
    Returns:
        Ligne avec accords ajoutés tout au long
    """
    if not notes or not chord:
        return f'"{chord}" {line}'  # Au moins un accord au début
    
    # Nettoyer la ligne (retirer les accords existants pour éviter les doublons)
    cleaned_line = re.sub(r'"[^"]*"\s*', '', line)
    cleaned_line = re.sub(r'![^!]*!\s*', '', cleaned_line)  # Retirer aussi les nuances
    
    # Parser la ligne en préservant les espaces
    # Pattern pour matcher les notes avec leurs durées
    pattern = r'([A-Ga-g][#b]?[0-9]*[/0-9]*)'
    
    # Trouver toutes les positions des notes
    note_positions = []
    for match in re.finditer(pattern, cleaned_line):
        note_positions.append((match.start(), match.end(), match.group(1)))
    
    if not note_positions:
        return f'"{chord}" {cleaned_line}'
    
    # Construire le résultat en insérant les accords
    result = []
    last_pos = 0
    
    # Ajouter un accord au début
    result.append(f'"{chord}" ')
    
    for i, (start, end, note) in enumerate(note_positions):
        # Ajouter le texte avant la note
        if start > last_pos:
            result.append(cleaned_line[last_pos:start])
        
        # Ajouter la note
        result.append(note)
        
        # Ajouter un accord tous les 2 notes (après la note, avec espace)
        if (i + 1) % 2 == 0 and i < len(note_positions) - 1:
            result.append(f' "{chord}"')
        
        last_pos = end
    
    # Ajouter le reste de la ligne
    if last_pos < len(cleaned_line):
        result.append(cleaned_line[last_pos:])
    
    return ''.join(result)


def add_dynamics_throughout_line(line: str, position: int) -> str:
    """
    Ajoute des nuances dynamiques tout au long d'une ligne.
    Évite d'insérer dans les arpèges [ ].
    
    Args:
        line: Ligne de notation ABC
        position: Position dans la pièce
    
    Returns:
        Ligne avec nuances ajoutées
    """
    # Retirer les nuances existantes pour éviter les doublons
    cleaned_line = re.sub(r'![^!]*!\s*', '', line)
    
    # Protéger les arpèges [ ] pour ne pas y insérer de nuances
    arpeggios = []
    arp_pattern = r'\[([^\]]+)\]'
    
    def replace_arpeggio(match):
        idx = len(arpeggios)
        arpeggios.append(match.group(0))
        return f'__ARP{idx}__'
    
    # Remplacer temporairement les arpèges
    protected_line = re.sub(arp_pattern, replace_arpeggio, cleaned_line)
    
    # Extraire les notes (hors arpèges)
    notes = re.findall(r'([A-Ga-g][#b]?[0-9]*[/0-9]*)', protected_line)
    
    if len(notes) < 2:
        # Ligne trop courte, juste ajouter au début
        dynamics = ['p', 'mf', 'f', 'mp']
        dynamic = dynamics[position % len(dynamics)]
        # Restaurer les arpèges
        for i, arp in enumerate(arpeggios):
            protected_line = protected_line.replace(f'__ARP{i}__', arp)
        return f'!{dynamic}! {protected_line}'
    
    # Trouver les positions des notes (hors arpèges)
    note_positions = []
    for match in re.finditer(r'([A-Ga-g][#b]?[0-9]*[/0-9]*)', protected_line):
        note_positions.append((match.start(), match.end()))
    
    # Ajouter une nuance au début
    dynamics = ['p', 'mf', 'f', 'mp', 'cresc', 'dim']
    dynamic_start = dynamics[position % len(dynamics)]
    
    # Construire le résultat avec nuances au milieu
    result = []
    result.append(f'!{dynamic_start}! ')
    last_pos = 0
    
    for i, (start, end) in enumerate(note_positions):
        # Ajouter le texte avant la note
        if start > last_pos:
            result.append(protected_line[last_pos:start])
        
        # Ajouter la note
        result.append(protected_line[start:end])
        
        # Changer la nuance tous les 3-4 notes (mais pas à la fin)
        if (i + 1) % 3 == 0 and i < len(note_positions) - 1:
            dynamic_mid = dynamics[(position + i) % len(dynamics)]
            result.append(f' !{dynamic_mid}!')
        
        last_pos = end
    
    # Ajouter le reste
    if last_pos < len(protected_line):
        result.append(protected_line[last_pos:])
    
    # Restaurer les arpèges dans l'ordre inverse pour éviter les conflits
    result_str = ''.join(result)
    for i in range(len(arpeggios) - 1, -1, -1):
        result_str = result_str.replace(f'__ARP{i}__', arpeggios[i])
    
    return result_str


def add_articulations(line: str, position: int) -> str:
    """
    Ajoute des articulations (staccato, legato, accents) pour plus d'expression.
    
    Args:
        line: Ligne de notation ABC
        position: Position dans la pièce
    
    Returns:
        Ligne avec articulations ajoutées
    """
    # Articulations ABC: . (staccato), ~ (trill), u (up-bow), v (down-bow)
    # Ajouter des staccatos occasionnels pour variété
    notes_count = len(re.findall(r'([A-Ga-g][#b]?[0-9]*[/0-9]*)', line))
    
    if notes_count > 3 and position % 3 == 0:
        # Ajouter quelques staccatos (pas tous, pour variété)
        line = re.sub(r'([A-Ga-g][#b]?)([0-9]*)([/0-9]*)', r'\1\2\3.', line, count=min(2, notes_count // 2))
    
    return line


def add_phrasing_and_breaths(line: str) -> str:
    """
    Ajoute des phrasés et respirations pour plus de musicalité.
    
    Args:
        line: Ligne de notation ABC
    
    Returns:
        Ligne avec phrasés ajoutés
    """
    # Ajouter des barres de mesure et des pauses occasionnelles
    # Format ABC: z pour pause
    
    # Compter les notes
    notes = re.findall(r'([A-Ga-g][#b]?[0-9]*[/0-9]*)', line)
    
    if len(notes) > 6:
        # Ajouter une petite pause au milieu pour respiration
        mid_point = len(line) // 2
        # Trouver une position appropriée (après une note)
        for i in range(mid_point, len(line)):
            if re.match(r'[A-Ga-g]', line[i]):
                line = line[:i+1] + ' z ' + line[i+1:]
                break
    
    return line
