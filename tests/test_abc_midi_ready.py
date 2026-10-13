"""Tests for MIDI-ready ABC preparation."""

from src.utils.abc_validator import (
    clean_abc_for_midi,
    ensure_midi_ready_abc,
    validate_abc_for_midi,
)


def test_clean_adds_required_headers_and_notes():
    cleaned = clean_abc_for_midi("garbage !!!")
    assert "X:1" in cleaned
    assert "M:" in cleaned
    assert "L:" in cleaned
    assert "K:" in cleaned
    ok, err = validate_abc_for_midi(cleaned)
    assert ok is True
    assert err is None


def test_ensure_midi_ready_on_messy_generation():
    messy = """X:1
X:99
M:nope
K:Cxyz
@@@ invalid $$$
C D E"""
    abc, ok, err = ensure_midi_ready_abc(messy, default_key="C", default_meter="4/4")
    assert ok is True
    assert err is None
    assert abc.count("X:") == 1
    assert "M:4/4" in abc or "M:" in abc
    assert "K:C" in abc
    assert any(ch.isalpha() and ch in "CDEFGABcdefgab" for ch in abc)


def test_ensure_midi_ready_preserves_valid_score():
    valid = """X:1
T:Test
M:3/4
L:1/8
K:G
GAB cde |"""
    abc, ok, err = ensure_midi_ready_abc(valid, default_key="C", default_meter="4/4")
    assert ok is True
    assert "M:3/4" in abc
    assert "K:G" in abc
