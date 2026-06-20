"""Tests for validators."""

import pytest

from src.utils.validators import (
    ValidationError,
    validate_temperature,
    validate_length,
    validate_key,
    validate_meter,
    validate_seed_string,
)


def test_validate_temperature_in_range():
    assert validate_temperature(0.8) == 0.8


def test_validate_temperature_out_of_range():
    with pytest.raises(ValidationError):
        validate_temperature(2.0)


def test_validate_length_in_range():
    assert validate_length(400) == 400


def test_validate_length_out_of_range():
    with pytest.raises(ValidationError):
        validate_length(50)


def test_validate_key_valid():
    assert validate_key("Am") == "Am"


def test_validate_key_invalid():
    with pytest.raises(ValidationError):
        validate_key("H")


def test_validate_meter_valid():
    assert validate_meter("3/4") == "3/4"


def test_validate_meter_invalid():
    with pytest.raises(ValidationError):
        validate_meter("5/4")


def test_validate_seed_string_valid():
    vocab = {"X": 0, ":": 1, "1": 2, "\n": 3, "K": 4, "C": 5}
    assert validate_seed_string("X:1\nK:C", vocab) == "X:1\nK:C"


def test_validate_seed_string_invalid_char():
    vocab = {"X": 0}
    with pytest.raises(ValidationError):
        validate_seed_string("ABC", vocab)
