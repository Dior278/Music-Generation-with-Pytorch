"""Generation backends (audio and symbolic)."""

from .base import GenerationResult
from .audio_musicgen import MusicGenBackend
from .symbolic_lstm import SymbolicLSTMBackend

__all__ = [
    "GenerationResult",
    "MusicGenBackend",
    "SymbolicLSTMBackend",
]
