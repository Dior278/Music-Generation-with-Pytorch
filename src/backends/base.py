"""Shared types for music generation backends."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GenerationResult:
    """Result of a generation call."""

    mode: str
    message: str
    audio_path: Optional[str] = None
    midi_path: Optional[str] = None
    abc_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
