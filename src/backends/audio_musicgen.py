"""MusicGen text-to-audio backend (pretrained, no local training)."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from src.backends.base import GenerationResult
from src.config import get_config

logger = logging.getLogger(__name__)


class MusicGenBackend:
    """Lazy-loaded MusicGen wrapper for text-to-WAV generation."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        config = get_config()
        self.model_id = model_id or config.get(
            "audio.model_id", "facebook/musicgen-small"
        )
        self.output_dir = Path(
            output_dir or config.get("paths.output", "outputs")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        device_pref = device or config.get("audio.device", "auto")
        if device_pref == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device_pref

        self.min_duration = int(config.get("audio.min_duration", 5))
        self.max_duration = int(config.get("audio.max_duration", 15))
        self.default_duration = int(config.get("audio.default_duration", 8))

        self._processor = None
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Download and load the pretrained MusicGen model."""
        if self.is_loaded:
            return

        from transformers import AutoProcessor, MusicgenForConditionalGeneration

        logger.info("Loading MusicGen model %s on %s...", self.model_id, self.device)
        self._processor = AutoProcessor.from_pretrained(self.model_id)
        self._model = MusicgenForConditionalGeneration.from_pretrained(self.model_id)
        self._model.to(self.device)
        self._model.eval()
        logger.info("MusicGen ready.")

    def generate(
        self,
        prompt: str,
        duration: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> GenerationResult:
        """
        Generate a WAV file from a text prompt.

        Args:
            prompt: Text description of the music.
            duration: Length in seconds (clamped to config bounds).
            seed: Optional RNG seed for reproducibility.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return GenerationResult(
                mode="audio",
                message="Veuillez fournir une description textuelle.",
            )

        duration = float(duration if duration is not None else self.default_duration)
        duration = max(self.min_duration, min(self.max_duration, duration))

        self.load()

        if seed is not None:
            torch.manual_seed(int(seed))
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(int(seed))

        # MusicGen generates ~50 tokens per second of audio
        max_new_tokens = int(duration * 50)

        inputs = self._processor(
            text=[prompt],
            padding=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            audio_values = self._model.generate(**inputs, max_new_tokens=max_new_tokens)

        sampling_rate = self._model.config.audio_encoder.sampling_rate
        audio = audio_values[0, 0].cpu().numpy().astype(np.float32)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_path = self.output_dir / f"musicgen_{stamp}.wav"
        self._write_wav(wav_path, audio, sampling_rate)

        return GenerationResult(
            mode="audio",
            message=f"Audio généré ({duration:.0f}s) — {wav_path.name}",
            audio_path=str(wav_path),
            metadata={
                "prompt": prompt,
                "duration": duration,
                "seed": seed,
                "sample_rate": sampling_rate,
                "model_id": self.model_id,
                "device": self.device,
            },
        )

    @staticmethod
    def _write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
        from scipy.io import wavfile

        # Clip and convert to 16-bit PCM
        clipped = np.clip(audio, -1.0, 1.0)
        pcm = (clipped * 32767).astype(np.int16)
        wavfile.write(str(path), sample_rate, pcm)
