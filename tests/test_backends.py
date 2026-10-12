"""Tests for generation backends (MusicGen mocked)."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from src.backends.base import GenerationResult
from src.backends.audio_musicgen import MusicGenBackend
from src.backends.symbolic_lstm import SymbolicLSTMBackend

TEST_OUT = Path(__file__).resolve().parent / "_tmp_backend_out"


def _fresh_outdir() -> Path:
    if TEST_OUT.exists():
        shutil.rmtree(TEST_OUT, ignore_errors=True)
    TEST_OUT.mkdir(parents=True, exist_ok=True)
    return TEST_OUT


def test_generation_result_defaults():
    result = GenerationResult(mode="audio", message="ok")
    assert result.audio_path is None
    assert result.midi_path is None
    assert result.abc_text is None
    assert result.metadata == {}


def test_musicgen_rejects_empty_prompt():
    out = _fresh_outdir()
    backend = MusicGenBackend(output_dir=str(out))
    result = backend.generate(prompt="   ")
    assert result.mode == "audio"
    assert result.audio_path is None
    assert "fournir" in result.message.lower()


def test_musicgen_generate_mocked():
    out = _fresh_outdir()
    backend = MusicGenBackend(output_dir=str(out), device="cpu")

    fake_audio = np.zeros(8000, dtype=np.float32)

    cell = MagicMock()
    cell.cpu.return_value.numpy.return_value = fake_audio
    audio_values = MagicMock()
    audio_values.__getitem__ = MagicMock(return_value=cell)

    mock_model = MagicMock()
    mock_model.config.audio_encoder.sampling_rate = 16000
    mock_model.generate.return_value = audio_values

    tensor = MagicMock()
    tensor.to.return_value = tensor
    mock_processor = MagicMock(return_value={"input_ids": tensor})

    with patch.object(backend, "load"):
        backend._processor = mock_processor
        backend._model = mock_model
        result = backend.generate(prompt="calm piano", duration=8, seed=42)

    assert result.mode == "audio"
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert result.metadata["prompt"] == "calm piano"
    assert result.metadata["duration"] == 8.0
    mock_model.generate.assert_called_once()


def test_symbolic_missing_weights():
    out = _fresh_outdir()
    backend = SymbolicLSTMBackend(
        model_path=str(out / "missing.pth"),
        vocab_path=str(out / "missing.json"),
        output_dir=str(out),
    )
    assert backend.weights_available() is False
    result = backend.generate()
    assert result.mode == "symbolic"
    assert result.midi_path is None
    assert "introuvables" in result.message.lower() or "Placez" in result.message


def test_audio_config_loaded():
    from src.config import get_config

    config = get_config()
    assert config.get("audio.model_id") == "facebook/musicgen-small"
    assert config.get("audio.default_duration") == 8
