"""Symbolic LSTM backend (ABC notation + MIDI)."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.backends.base import GenerationResult
from src.config import get_config
from src.utils.abc_validator import ensure_midi_ready_abc
from src.utils.midi_converter import abc_to_midi

logger = logging.getLogger(__name__)


class SymbolicLSTMBackend:
    """Lazy-loaded wrapper around the trained LSTM MusicGenerator."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        config = get_config()
        self.model_path = model_path or config.get("paths.model", "best_model.pth")
        self.vocab_path = vocab_path or config.get("paths.vocab", "vocab.json")
        self.output_dir = Path(
            output_dir or config.get("paths.output", "outputs")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._generator = None

    @property
    def is_loaded(self) -> bool:
        return self._generator is not None

    def weights_available(self) -> bool:
        return Path(self.model_path).exists() and Path(self.vocab_path).exists()

    def load(self) -> None:
        if self.is_loaded:
            return
        if not self.weights_available():
            raise FileNotFoundError(
                f"Poids LSTM introuvables. Placez {self.model_path} et "
                f"{self.vocab_path} à la racine du projet "
                "(voir notebooks/train_lstm_colab.ipynb)."
            )
        from src.generation.music_generator import MusicGenerator

        self._generator = MusicGenerator(
            model_path=self.model_path,
            vocab_path=self.vocab_path,
        )
        logger.info("Symbolic LSTM backend ready.")

    def generate(
        self,
        temperature: float = 0.8,
        length: int = 400,
        key: str = "C",
        meter: str = "4/4",
        seed: Optional[str] = None,
    ) -> GenerationResult:
        """Generate ABC notation and a MIDI file."""
        try:
            self.load()
        except FileNotFoundError as exc:
            return GenerationResult(mode="symbolic", message=str(exc))

        seed_text = seed.strip() if seed and seed.strip() else None

        try:
            abc_text = self._generator.generate(
                seed=seed_text,
                temperature=float(temperature),
                length=int(length),
                key=key,
                meter=meter,
            )
        except Exception as exc:
            logger.exception("Symbolic generation failed")
            return GenerationResult(
                mode="symbolic",
                message=f"Erreur lors de la génération : {exc}",
            )

        abc_text, midi_ready, prep_err = ensure_midi_ready_abc(
            abc_text, default_key=key, default_meter=meter
        )
        if not midi_ready:
            logger.warning("ABC preparation failed: %s", prep_err)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        midi_path = self.output_dir / f"lstm_{stamp}.mid"
        abc_path = self.output_dir / f"lstm_{stamp}.abc"

        with open(abc_path, "w", encoding="utf-8") as f:
            f.write(abc_text)

        if not abc_to_midi(abc_text, midi_path):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
            tmp.close()
            if abc_to_midi(abc_text, tmp.name):
                return GenerationResult(
                    mode="symbolic",
                    message="Musique générée (MIDI temporaire, format ABC corrigé).",
                    abc_text=abc_text,
                    midi_path=tmp.name,
                    metadata={"abc_path": str(abc_path), "midi_ready": midi_ready},
                )
            return GenerationResult(
                mode="symbolic",
                message="ABC généré mais conversion MIDI impossible même après correction.",
                abc_text=abc_text,
                metadata={"midi_ready": False, "error": prep_err},
            )

        status = f"Musique générée — {midi_path.name}"
        if midi_ready:
            status += " (format ABC vérifié)"
        return GenerationResult(
            mode="symbolic",
            message=status,
            abc_text=abc_text,
            midi_path=str(midi_path),
            metadata={"abc_path": str(abc_path), "midi_ready": midi_ready},
        )
