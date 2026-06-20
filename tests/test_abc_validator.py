"""Tests for ABC validation and cleaning."""

from src.utils.abc_validator import clean_abc_for_midi, validate_abc_for_midi


SAMPLE_ABC = """X:1
M:4/4
L:1/8
K:C
CDEF GABc |"""


def test_validate_abc_for_midi_valid():
    is_valid, error = validate_abc_for_midi(SAMPLE_ABC)
    assert is_valid is True
    assert error is None


def test_validate_abc_for_midi_missing_key():
    is_valid, error = validate_abc_for_midi("X:1\nCDEF")
    assert is_valid is False
    assert "K:" in error


def test_clean_abc_for_midi_adds_missing_headers():
    cleaned = clean_abc_for_midi("K:C\nCDEF")
    assert "X:1" in cleaned
    assert "K:C" in cleaned
    assert "M:4/4" in cleaned
    assert "L:1/8" in cleaned


def test_clean_abc_for_midi_removes_duplicate_headers():
    dirty = """X:1
X:2
M:4/4
M:3/4
K:C
K:G
CDEF"""
    cleaned = clean_abc_for_midi(dirty)
    assert cleaned.count("X:") == 1
    assert cleaned.count("M:") == 1
    assert cleaned.count("K:") == 1
