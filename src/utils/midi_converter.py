"""
Utilities for conversion between ABC and MIDI formats.

This module handles conversion between ABC notation and MIDI files
using the music21 library.
"""

from pathlib import Path
from typing import Optional, Union
from music21 import converter, stream
import logging

logger = logging.getLogger(__name__)


def abc_to_midi(abc_text: str, output_filename: Union[str, Path]) -> bool:
    """
    Convertit une notation ABC en fichier MIDI.
    Gère les problèmes de duplication d'objets music21.
    
    Args:
        abc_text: Notation ABC sous forme de chaîne
        output_filename: Chemin du fichier MIDI de sortie
    
    Returns:
        True si la conversion a réussi, False sinon
    """
    try:
        # Parser la notation ABC
        score = converter.parse(abc_text, format='abc')
        
        # Nettoyer les duplications dans le Stream
        # music21 peut créer des objets dupliqués (TimeSignature, KeySignature, etc.)
        def remove_duplicates_from_stream(stream_obj):
            """Supprime les objets dupliqués d'un Stream."""
            seen_ids = set()
            elements_to_remove = []
            
            for element in stream_obj.elements:
                element_id = id(element)
                if element_id in seen_ids:
                    elements_to_remove.append(element)
                else:
                    seen_ids.add(element_id)
                    # Récursivement nettoyer les sous-streams
                    if hasattr(element, 'elements'):
                        remove_duplicates_from_stream(element)
            
            # Supprimer les éléments dupliqués
            for element in elements_to_remove:
                try:
                    stream_obj.remove(element)
                except:
                    pass
        
        # Nettoyer le score et ses parties
        if hasattr(score, 'parts'):
            for part in score.parts:
                remove_duplicates_from_stream(part)
                
                # Supprimer spécifiquement les TimeSignature dupliqués
                time_sigs = part.getElementsByClass('TimeSignature')
                if len(time_sigs) > 1:
                    # Garder seulement le premier, supprimer les autres
                    for ts in time_sigs[1:]:
                        try:
                            part.remove(ts)
                        except:
                            pass
                
                # Supprimer les KeySignature dupliqués
                key_sigs = part.getElementsByClass('KeySignature')
                if len(key_sigs) > 1:
                    # Garder seulement le premier, supprimer les autres
                    for ks in key_sigs[1:]:
                        try:
                            part.remove(ks)
                        except:
                            pass
        
        # Alternative: créer un nouveau Stream propre
        try:
            # S'assurer que le répertoire de sortie existe
            output_path = Path(output_filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder en MIDI
            score.write('midi', fp=str(output_path))
            
            logger.info(f"Conversion ABC -> MIDI réussie: {output_filename}")
            return True
        except Exception as write_error:
            # Si l'erreur persiste, essayer avec un Stream simplifié
            logger.warning(f"Erreur lors de l'écriture MIDI, tentative avec Stream simplifié: {write_error}")
            
            # Créer un nouveau Stream propre
            from music21 import stream, meter, key
            new_score = stream.Score()
            
            # Extraire les métadonnées du score original
            if hasattr(score, 'metadata'):
                new_score.metadata = score.metadata
            
            # Créer une nouvelle partie
            new_part = stream.Part()
            
            # Ajouter les éléments musicaux (notes, accords) sans les métadonnées dupliquées
            for element in score.flat.notes:
                new_part.append(element)
            
            # Ajouter une seule TimeSignature et KeySignature
            if score.flat.getElementsByClass('TimeSignature'):
                ts = score.flat.getElementsByClass('TimeSignature')[0]
                new_part.insert(0, ts)
            else:
                new_part.insert(0, meter.TimeSignature('4/4'))
            
            if score.flat.getElementsByClass('KeySignature'):
                ks = score.flat.getElementsByClass('KeySignature')[0]
                new_part.insert(0, ks)
            
            new_score.append(new_part)
            
            # Sauvegarder
            new_score.write('midi', fp=str(output_path))
            logger.info(f"Conversion ABC -> MIDI réussie (Stream simplifié): {output_filename}")
            return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion ABC -> MIDI: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def midi_to_abc(midi_file: Union[str, Path], output_filename: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Convertit un fichier MIDI en notation ABC.
    
    Args:
        midi_file: Chemin vers le fichier MIDI
        output_filename: Chemin du fichier ABC de sortie (optionnel)
    
    Returns:
        Notation ABC sous forme de chaîne, ou None en cas d'erreur
    """
    try:
        # Parser le fichier MIDI
        score = converter.parse(str(midi_file))
        
        # Convertir en ABC
        abc_text = score.write('abc')
        
        # Sauvegarder si un fichier de sortie est spécifié
        if output_filename:
            output_path = Path(output_filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(abc_text)
            logger.info(f"Conversion MIDI -> ABC réussie: {output_filename}")
        
        return abc_text
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion MIDI -> ABC: {e}")
        return None
