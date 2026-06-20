"""
Music generator using an LSTM model.

This module contains the main class for generating music
from a trained model.
"""

import torch
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

from src.models.lstm_model import MusicLSTM
from src.utils.validators import (
    validate_temperature,
    validate_length,
    validate_key,
    validate_meter,
    validate_seed_string,
    ValidationError
)
from src.utils.midi_converter import abc_to_midi
from src.config import get_config

logger = logging.getLogger(__name__)


class MusicGenerator:
    """
    Music generator using an LSTM model.
    
    This class encapsulates the music generation logic,
    including model loading, parameter validation,
    and the generation process itself.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
        device: Optional[torch.device] = None
    ):
        """
        Initialize the music generator.
        
        Args:
            model_path: Path to the model file (.pth)
            vocab_path: Path to the vocabulary file (vocab.json)
            device: PyTorch device (CPU or GPU)
        """
        self.config = get_config()
        
        # Déterminer le device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # File paths
        self.model_path = model_path or self.config.get("paths.model", "best_model.pth")
        self.vocab_path = vocab_path or self.config.get("paths.vocab", "vocab.json")
        
        # Load model and vocabulary
        self.model = None
        self.char2idx = None
        self.idx2char = None
        self.vocab_size = None
        
        self._load_model()
        self._load_vocab()
    
    def _load_model(self):
        """Load the model from file."""
        try:
            import json
            
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Get vocabulary size from checkpoint or config
            vocab_size = checkpoint.get('vocab_size')
            if vocab_size is None:
                # Try loading from vocabulary file
                with open(self.vocab_path, 'r', encoding='utf-8') as f:
                    vocab_info = json.load(f)
                    vocab_size = vocab_info['vocab_size']
            
            # Automatically detect model parameters from saved weights
            state_dict = checkpoint['model_state_dict']
            
            # Detect embedding_dim from embedding weights
            embedding_weight = state_dict.get('embedding.weight')
            if embedding_weight is not None:
                embedding_dim = embedding_weight.shape[1]
            else:
                # Fallback to config
                model_config = self.config.get("model", {})
                embedding_dim = model_config.get("embedding_dim", 128)
            
            # Detect hidden_dim from LSTM weights
            # LSTM weight_ih shape: (4*hidden_dim, embedding_dim)
            lstm_weight_ih = state_dict.get('lstm.weight_ih_l0')
            if lstm_weight_ih is not None:
                hidden_dim = lstm_weight_ih.shape[0] // 4
            else:
                # Fallback to config
                model_config = self.config.get("model", {})
                hidden_dim = model_config.get("hidden_dim", 256)
            
            # Detect num_layers by counting LSTM layers
            num_layers = 0
            for key in state_dict.keys():
                if key.startswith('lstm.weight_ih_l'):
                    try:
                        layer_num = int(key.split('_l')[1].split('_')[0])
                        num_layers = max(num_layers, layer_num + 1)
                    except (ValueError, IndexError):
                        pass
            
            if num_layers == 0:
                # Fallback to config
                model_config = self.config.get("model", {})
                num_layers = model_config.get("num_layers", 2)
            
            # Dropout from config (difficult to detect from weights)
            model_config = self.config.get("model", {})
            dropout = model_config.get("dropout", 0.3)
            
            logger.info(f"Automatic model parameter detection:")
            logger.info(f"  embedding_dim: {embedding_dim}")
            logger.info(f"  hidden_dim: {hidden_dim}")
            logger.info(f"  num_layers: {num_layers}")
            logger.info(f"  vocab_size: {vocab_size}")
            
            # Create model with detected parameters
            self.model = MusicLSTM(
                vocab_size=vocab_size,
                embedding_dim=embedding_dim,
                hidden_dim=hidden_dim,
                num_layers=num_layers,
                dropout=dropout
            ).to(self.device)
            
            # Load weights
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            self.vocab_size = vocab_size
            
            logger.info(f"Model loaded from {self.model_path}")
            logger.info(f"Parameters: {self.model.get_num_parameters():,}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _load_vocab(self):
        """Load vocabulary from JSON file."""
        try:
            import json
            
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                vocab_info = json.load(f)
            
            self.char2idx = vocab_info['char2idx']
            self.idx2char = {int(k): v for k, v in vocab_info['idx2char'].items()}
            
            logger.info(f"Vocabulary loaded: {len(self.char2idx)} characters")
            
        except Exception as e:
            logger.error(f"Error loading vocabulary: {e}")
            raise
    
    def generate(
        self,
        seed: Optional[str] = None,
        temperature: float = 0.8,
        length: int = 400,
        key: str = "C",
        meter: str = "4/4"
    ) -> str:
        """
        Generate music from given parameters.
        
        Args:
            seed: Starting string (optional, auto-generated if None)
            temperature: Controls creativity (0.5 = conservative, 1.5 = creative)
            length: Number of characters to generate
            key: Musical key (C, D, G, etc.)
            meter: Time signature (2/4, 3/4, 4/4, 6/8)
        
        Returns:
            Generated ABC notation
        
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate parameters
        try:
            temperature = validate_temperature(temperature)
            length = validate_length(length)
            key = validate_key(key)
            meter = validate_meter(meter)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        
        # Generate seed if not provided
        if seed is None:
            seed = f"X:1\nL:1/8\nM:{meter}\nK:{key}\n"
        else:
            validate_seed_string(seed, self.char2idx)
        
        logger.info(f"Generation with temperature={temperature}, length={length}, key={key}, meter={meter}")
        
        # Convert seed to indices
        try:
            input_eval = [self.char2idx[c] for c in seed if c in self.char2idx]
            if len(input_eval) == 0:
                raise ValueError("No valid characters in seed")
            # Shape: (batch_size=1, seq_len)
            input_eval = torch.tensor([input_eval], dtype=torch.long).to(self.device)
        except Exception as e:
            logger.error(f"Error converting seed: {e}")
            raise
        
        generated_text = seed
        hidden = None
        
        # Generation
        with torch.no_grad():
            for i in range(length):
                try:
                    output, hidden = self.model(input_eval, hidden)
                    
                    # Take the last prediction
                    # output shape: (batch_size, seq_len, vocab_size)
                    output = output[:, -1, :] / temperature
                    probabilities = torch.softmax(output, dim=-1)
                    
                    # Sample according to probabilities
                    # predicted_id shape: (batch_size=1, 1)
                    predicted_id = torch.multinomial(probabilities, 1)
                    
                    # Add predicted character
                    predicted_idx = predicted_id.item()
                    if predicted_idx in self.idx2char:
                        predicted_char = self.idx2char[predicted_idx]
                        generated_text += predicted_char
                    else:
                        logger.warning(f"Predicted index {predicted_idx} not found in idx2char")
                        break
                    
                    # Prepare input for next iteration
                    # predicted_id shape: (1, 1), keep as (1, 1)
                    # No need to reshape, already correct
                    input_eval = predicted_id
                    
                except Exception as e:
                    logger.error(f"Error during generation (iteration {i}): {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    break
        
        logger.info(f"Generation completed: {len(generated_text)} characters")
        
        # Basic post-processing to improve format
        generated_text = self._clean_abc_output(generated_text)
        
        # Enrich with harmonic chords (high density for classical style)
        try:
            from src.utils.chord_enhancer import enhance_with_chords
            generated_text = enhance_with_chords(
                generated_text, 
                chord_density=0.9,  # High density for more chords
                use_smart_chords=True
            )
            logger.info("Harmonic chords, arpeggios and dynamics added successfully")
        except Exception as e:
            logger.warning(f"Unable to add chords: {e}")
        
        # Validate and clean to ensure MIDI conversion
        try:
            from src.utils.abc_validator import clean_abc_for_midi, validate_abc_for_midi
            is_valid, error_msg = validate_abc_for_midi(generated_text)
            if not is_valid:
                logger.warning(f"Invalid ABC detected: {error_msg}, cleaning...")
            generated_text = clean_abc_for_midi(generated_text)
            logger.info("ABC notation validated and cleaned for MIDI conversion")
        except Exception as e:
            logger.warning(f"Error during ABC validation: {e}")
        
        return generated_text
    
    def _clean_abc_output(self, abc_text: str) -> str:
        """
        Clean and format ABC output to improve quality.
        
        Args:
            abc_text: Raw generated ABC text
            
        Returns:
            Cleaned ABC text
        """
        lines = abc_text.split('\n')
        cleaned_lines = []
        seen_header = set()
        
        # Keep valid header lines
        header_keys = ['X:', 'T:', 'M:', 'L:', 'K:', 'Q:', 'R:', 'C:']
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ligne d'en-tête
            if any(line.startswith(key) for key in header_keys):
                key = line.split(':')[0] + ':'
                if key not in seen_header:
                    cleaned_lines.append(line)
                    seen_header.add(key)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def generate_and_save(
        self,
        output_path: str,
        seed: Optional[str] = None,
        temperature: float = 0.8,
        length: int = 400,
        key: str = "C",
        meter: str = "4/4",
        save_midi: bool = True
    ) -> Tuple[str, Optional[str]]:
        """
        Generate music and save to files.
        
        Args:
            output_path: Base path for output files
            seed: Starting string (optional)
            temperature: Generation temperature
            length: Generation length
            key: Musical key
            meter: Time signature
            save_midi: If True, also save MIDI file
        
        Returns:
            Tuple (abc_path, midi_path or None)
        """
        # Generate music
        abc_text = self.generate(seed, temperature, length, key, meter)
        
        # Save ABC file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        abc_file = output_path.with_suffix('.abc')
        with open(abc_file, 'w', encoding='utf-8') as f:
            f.write(abc_text)
        
        logger.info(f"ABC file saved: {abc_file}")
        
        # Save MIDI file if requested
        midi_file = None
        if save_midi:
            midi_file = output_path.with_suffix('.mid')
            if abc_to_midi(abc_text, midi_file):
                logger.info(f"MIDI file saved: {midi_file}")
            else:
                logger.warning(f"MIDI conversion failed")
                midi_file = None
        
        return str(abc_file), str(midi_file) if midi_file else None
