"""
Harmonic enrichment module for ABC notation.

This module adds harmonic chords to a monophonic melody
to make the music richer and more interesting.
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# Chord progressions by key
CHORD_PROGRESSIONS = {
    'C': {
        'major': ['C', 'Am', 'F', 'G', 'C', 'Am', 'Dm', 'G'],
        'minor': ['Am', 'Dm', 'G', 'C', 'Am', 'F', 'C', 'G']
    },
    'D': {
        'major': ['D', 'Bm', 'G', 'A', 'D', 'Bm', 'Em', 'A'],
        'minor': ['Bm', 'Em', 'A', 'D', 'Bm', 'G', 'D', 'A']
    },
    'E': {
        'major': ['E', 'C#m', 'A', 'B', 'E', 'C#m', 'F#m', 'B'],
        'minor': ['C#m', 'F#m', 'B', 'E', 'C#m', 'A', 'E', 'B']
    },
    'F': {
        'major': ['F', 'Dm', 'Bb', 'C', 'F', 'Dm', 'Gm', 'C'],
        'minor': ['Dm', 'Gm', 'C', 'F', 'Dm', 'Bb', 'F', 'C']
    },
    'G': {
        'major': ['G', 'Em', 'C', 'D', 'G', 'Em', 'Am', 'D'],
        'minor': ['Em', 'Am', 'D', 'G', 'Em', 'C', 'G', 'D']
    },
    'A': {
        'major': ['A', 'F#m', 'D', 'E', 'A', 'F#m', 'Bm', 'E'],
        'minor': ['Am', 'Dm', 'G', 'C', 'Am', 'F', 'C', 'G']
    },
    'B': {
        'major': ['B', 'G#m', 'E', 'F#', 'B', 'G#m', 'C#m', 'F#'],
        'minor': ['Bm', 'Em', 'A', 'D', 'Bm', 'G', 'D', 'A']
    }
}

# Note to chord mapping
NOTE_TO_CHORD = {
    'C': ['C', 'Am', 'F'],
    'D': ['D', 'Bm', 'G'],
    'E': ['E', 'C#m', 'A'],
    'F': ['F', 'Dm', 'Bb'],
    'G': ['G', 'Em', 'C'],
    'A': ['A', 'F#m', 'D'],
    'B': ['B', 'G#m', 'E']
}


def extract_key_from_abc(abc_text: str) -> str:
    """Extrait la tonalité depuis la notation ABC."""
    for line in abc_text.split('\n'):
        if line.startswith('K:'):
            key = line[2:].strip()
            # Nettoyer la tonalité (enlever les octaves, etc.)
            if key and key[0].isalpha():
                return key[0].upper()
    return 'C'  # Par défaut


def is_minor_key(key: str) -> bool:
    """Détermine si la tonalité est mineure."""
    return 'm' in key.lower() or key in ['Am', 'Bm', 'Cm', 'Dm', 'Em', 'Fm', 'Gm']


def parse_abc_notes(abc_line: str) -> List[Tuple[str, float]]:
    """
    Parse une ligne ABC et extrait les notes avec leur durée.
    
    Returns:
        Liste de tuples (note, durée) où durée est en fraction (1/8, 1/4, etc.)
    """
    notes = []
    # Pattern pour matcher les notes ABC: [A-G][#b]?[0-9]?[/0-9]?
    pattern = r'([A-Ga-g][#b]?)([0-9]*)(/[0-9]*)?'
    
    matches = re.finditer(pattern, abc_line)
    for match in matches:
        note = match.group(1).upper()
        duration_num = match.group(2)
        duration_denom = match.group(3)
        
        # Calculer la durée
        if duration_num:
            num = int(duration_num)
        else:
            num = 1
        
        if duration_denom:
            denom = int(duration_denom[1:])
        else:
            denom = 8  # Par défaut 1/8
        
        duration = num / denom
        notes.append((note, duration))
    
    return notes


def get_chord_for_note(note: str, key: str, progression: List[str], position: int) -> str:
    """
    Détermine l'accord à utiliser pour une note donnée.
    
    Args:
        note: Note de la mélodie
        key: Tonalité
        progression: Chord progression
        position: Position dans la progression
    
    Returns:
        Nom de l'accord (ex: "C", "Am", "G7")
    """
    if not progression:
        return ''
    
    # Utiliser la progression cyclique
    chord_index = position % len(progression)
    return progression[chord_index]


def add_arpeggio_notes(abc_line: str, chord: str, style: str = "classical") -> str:
    """
    Ajoute des arpèges à une ligne de musique.
    
    Args:
        abc_line: Ligne de notation ABC
        chord: Accord à arpéger
        style: Style d'arpège ("classical", "simple")
    
    Returns:
        Ligne avec arpèges ajoutés
    """
    if not chord or not abc_line.strip():
        return abc_line
    
    # Extraire les notes de l'accord
    chord_notes = {
        'C': 'C E G',
        'Am': 'A C E',
        'F': 'F A C',
        'G': 'G B D',
        'D': 'D F# A',
        'Em': 'E G B',
        'Dm': 'D F A',
        'Bb': 'Bb D F',
        'A': 'A C# E',
        'Bm': 'B D F#',
        'E': 'E G# B',
        'F#': 'F# A# C#',
        'C#m': 'C# E G#',
        'G#m': 'G# B D#',
        'C#': 'C# E# G#',
        'F#m': 'F# A C#',
        'B': 'B D# F#',
    }
    
    # Obtenir les notes de l'accord
    notes = chord_notes.get(chord, '')
    if not notes:
        return abc_line
    
    # Style classique: arpège avant la mélodie
    if style == "classical":
        # Ajouter un arpège court au début
        arp = f"[{notes}]"
        return f'{arp} {abc_line}'
    
    return abc_line


def add_dynamic_marks(abc_line: str, position: int) -> str:
    """
    Ajoute des nuances dynamiques (piano, forte, etc.) style classique.
    
    Args:
        abc_line: Ligne de notation ABC
        position: Position dans la pièce
    
    Returns:
        Ligne avec nuances ajoutées
    """
    # Alterner les nuances pour créer de la variété
    dynamics = ['p', 'mf', 'f', 'mp', 'p', 'f', 'mf', 'p']
    dynamic = dynamics[position % len(dynamics)]
    
    # Ajouter la nuance au début de la ligne (format ABC: !p!, !f!, etc.)
    if abc_line.strip() and not abc_line.strip().startswith('!'):
        return f'!{dynamic}! {abc_line}'
    
    return abc_line


def add_chords_to_abc(abc_text: str, chord_density: float = 0.9, add_arpeggios: bool = True, add_dynamics: bool = True) -> str:
    """
    Adds harmonic chords, arpeggios and dynamics to a monophonic ABC notation.
    
    Args:
        abc_text: ABC notation without chords
        chord_density: Chord density (0.0 = none, 1.0 = maximum, 0.9 = many)
        add_arpeggios: If True, adds classical-style arpeggios
        add_dynamics: If True, adds dynamic nuances (p, f, mf, etc.)
    
    Returns:
        ABC notation with chords, arpeggios and dynamics added
    """
    lines = abc_text.split('\n')
    result_lines = []
    
    # Extract key
    key = extract_key_from_abc(abc_text)
    is_minor = is_minor_key(key)
    
    # Get chord progression
    base_key = key[0] if key else 'C'
    if base_key not in CHORD_PROGRESSIONS:
        base_key = 'C'
    
    progression = CHORD_PROGRESSIONS[base_key].get('minor' if is_minor else 'major', 
                                                    CHORD_PROGRESSIONS[base_key]['major'])
    
    in_body = False
    chord_position = 0
    notes_count = 0
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Copier les lignes d'en-tête telles quelles
        if line.startswith(('X:', 'T:', 'M:', 'L:', 'K:', 'Q:', 'R:', 'C:')):
            result_lines.append(original_line)
            if line.startswith('K:'):
                in_body = True
            continue
        
        # Ignorer les lignes vides
        if not line:
            result_lines.append('')
            continue
        
        # Traiter les lignes de musique
        if in_body or (line and not line.startswith('%')):
            # Parser les notes de la ligne
            notes = parse_abc_notes(line)
            
            if notes:
                # Always add a chord with density 0.9
                chord = get_chord_for_note(notes[0][0], key, progression, chord_position)
                
                if chord:
                    # Enrich line with musical expression throughout
                    from src.utils.musical_expression import (
                        add_chords_throughout_line,
                        add_dynamics_throughout_line,
                        add_articulations,
                        add_phrasing_and_breaths
                    )
                    
                    # Clean line first (remove existing chords and dynamics)
                    clean_line = re.sub(r'"[^"]*"\s*', '', line)
                    clean_line = re.sub(r'![^!]*!\s*', '', clean_line)
                    
                    # 1. Add chords throughout the line (not just at the beginning)
                    if chord_density >= 0.8:
                        line_with_chords = add_chords_throughout_line(clean_line, chord, [n[0] for n in notes])
                    else:
                        # Otherwise just at the beginning
                        line_with_chords = f'"{chord}" {clean_line}'
                    
                    # 2. Add arpeggios if requested (BEFORE dynamics)
                    if add_arpeggios and chord_position % 2 == 0:
                        line = add_arpeggio_notes(line_with_chords, chord, style="classical")
                    else:
                        line = line_with_chords
                    
                    # 3. Add dynamic nuances throughout the line (AFTER chords and arpeggios)
                    if add_dynamics:
                        line = add_dynamics_throughout_line(line, chord_position)
                    
                    # 4. Add articulations for more expression
                    if chord_position % 3 == 0:
                        line = add_articulations(line, chord_position)
                    
                    # 5. Add phrasing and breaths
                    if len(notes) > 4:
                        line = add_phrasing_and_breaths(line)
                    
                    chord_position += 1
                else:
                    chord_position += 1
                
                notes_count += len(notes)
                result_lines.append(line)
            else:
                result_lines.append(original_line)
        else:
            result_lines.append(original_line)
    
    return '\n'.join(result_lines)


def enhance_with_chords(abc_text: str, 
                       chord_density: float = 0.9,
                       use_smart_chords: bool = True) -> str:
    """
    Enriches ABC notation with harmonic chords, arpeggios and dynamics.
    
    Args:
        abc_text: Original ABC notation
        chord_density: Chord density (0.0-1.0, 0.9 = many chords)
        use_smart_chords: If True, uses smarter logic
    
    Returns:
        ABC notation enriched with chords, arpeggios and dynamics
    """
    try:
        if use_smart_chords:
            # Improved version with chords, arpeggios and classical-style dynamics
            return add_chords_to_abc(
                abc_text, 
                chord_density=chord_density,
                add_arpeggios=True,
                add_dynamics=True
            )
        else:
            return add_chords_to_abc(
                abc_text, 
                chord_density=chord_density,
                add_arpeggios=False,
                add_dynamics=False
            )
    except Exception as e:
        logger.warning(f"Error adding chords: {e}")
        return abc_text  # Return original on error
