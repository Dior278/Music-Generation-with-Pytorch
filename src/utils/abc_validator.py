"""
ABC notation validator and cleaner for MIDI compatibility.

Guarantees a convertible ABC score before music21 / MIDI export.
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

HEADER_ORDER = ("X:", "T:", "M:", "L:", "K:")
HEADER_PREFIXES = ("X:", "T:", "M:", "L:", "K:", "Q:", "R:", "C:", "%")


def clean_music_line(line: str) -> str:
    """Keep only MIDI-safe ABC body characters."""
    valid_chars = r"[A-Ga-g0-9/\s|\"'\-,\[\](){}#b=~.!<>:]"
    cleaned = ""
    i = 0
    while i < len(line):
        char = line[i]
        if char == '"':
            cleaned += char
            i += 1
            while i < len(line) and line[i] != '"':
                if line[i].isalnum() or line[i] in "#bm79/":
                    cleaned += line[i]
                i += 1
            if i < len(line) and line[i] == '"':
                cleaned += '"'
                i += 1
            else:
                cleaned += '"'
            continue
        if re.match(valid_chars, char):
            cleaned += char
        i += 1

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Close unbalanced quotes
    if cleaned.count('"') % 2 == 1:
        cleaned += '"'
    return cleaned


def _normalize_key(raw: str) -> str:
    key = re.sub(r"[^A-Ga-gm#]", "", (raw or "").strip())
    if not key:
        return "C"
    # Prefer forms like C, Am, F#m
    m = re.match(r"^([A-G][#b]?)(m)?", key)
    if not m:
        return "C"
    return f"{m.group(1)}{m.group(2) or ''}"


def clean_abc_for_midi(abc_text: str, default_key: str = "C", default_meter: str = "4/4") -> str:
    """
    Normalize ABC headers and body for MIDI conversion.

    Always returns a score with X/M/L/K and at least one music line when possible.
    """
    lines = (abc_text or "").split("\n")
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_body = False

    for raw in lines:
        line = raw.strip()
        if not line:
            if in_body:
                body_lines.append("")
            continue
        if line.startswith("%"):
            continue

        if line.startswith("X:"):
            if "X:" not in headers:
                value = line[2:].strip() or "1"
                headers["X:"] = f"X:{value}"
            continue
        if line.startswith("T:"):
            if "T:" not in headers:
                title = line[2:].strip() or "Generated"
                headers["T:"] = f"T:{title}"
            continue
        if line.startswith("M:"):
            if "M:" not in headers:
                meter = line[2:].strip()
                if not re.match(r"^\d+/\d+$", meter):
                    meter = default_meter
                headers["M:"] = f"M:{meter}"
            continue
        if line.startswith("L:"):
            if "L:" not in headers:
                length = line[2:].strip()
                if not re.match(r"^\d+/\d+$", length):
                    length = "1/8"
                headers["L:"] = f"L:{length}"
            continue
        if line.startswith("K:"):
            if "K:" not in headers:
                key = _normalize_key(line[2:])
                headers["K:"] = f"K:{key}"
                in_body = True
            continue

        # Drop stray headers after body started
        if in_body and line.startswith(("Q:", "R:", "C:", "M:", "L:", "K:", "X:", "T:")):
            continue

        if line.startswith(("Q:", "R:", "C:")):
            continue

        cleaned = clean_music_line(line)
        if cleaned:
            # Lines that look like headers slipped into body
            if cleaned.startswith(HEADER_PREFIXES):
                continue
            body_lines.append(cleaned)
            in_body = True

    # Required headers with defaults
    headers.setdefault("X:", "X:1")
    headers.setdefault("T:", "T:Studio")
    headers.setdefault("M:", f"M:{default_meter}")
    headers.setdefault("L:", "L:1/8")
    headers.setdefault("K:", f"K:{_normalize_key(default_key)}")

    # Ensure musical content
    body_lines = [b for b in body_lines if b is not None]
    has_notes = any(re.search(r"[A-Ga-g]", b) for b in body_lines)
    if not has_notes:
        key_letter = _normalize_key(headers["K:"][2:])[0]
        body_lines = [f"{key_letter}2 {key_letter}2 {key_letter}2 {key_letter}2 |"]

    ordered = [headers[h] for h in HEADER_ORDER if h in headers]
    return "\n".join(ordered + body_lines)


def validate_abc_for_midi(abc_text: str) -> Tuple[bool, Optional[str]]:
    """Structural validation before MIDI conversion."""
    if not abc_text or not abc_text.strip():
        return False, "Notation ABC vide"

    if "X:" not in abc_text:
        return False, "En-tête X: manquant"
    if "K:" not in abc_text:
        return False, "En-tête K: (tonalité) manquant"
    if "M:" not in abc_text:
        return False, "En-tête M: (mesure) manquant"
    if "L:" not in abc_text:
        return False, "En-tête L: (durée) manquant"

    has_music = False
    for line in abc_text.split("\n"):
        line = line.strip()
        if not line or line.startswith(HEADER_PREFIXES):
            continue
        if re.search(r"[A-Ga-g]", line):
            has_music = True
            break

    if not has_music:
        return False, "Aucune note musicale trouvée"

    return True, None


def verify_abc_parses(abc_text: str) -> Tuple[bool, Optional[str]]:
    """Try parsing with music21 (same path as MIDI conversion)."""
    try:
        from music21 import converter

        score = converter.parse(abc_text, format="abc")
        try:
            flat = score.flatten()
        except Exception:
            flat = score.flat
        notes = list(flat.notes)
        if not notes:
            return False, "Score vide après parse music21"
        return True, None
    except Exception as exc:
        return False, str(exc)


def ensure_midi_ready_abc(
    abc_text: str,
    default_key: str = "C",
    default_meter: str = "4/4",
) -> Tuple[str, bool, Optional[str]]:
    """
    Clean + validate + parse-check ABC until it is MIDI-ready.

    Returns:
        (abc_text, ok, error_or_warning)
    """
    cleaned = clean_abc_for_midi(abc_text, default_key=default_key, default_meter=default_meter)
    ok, err = validate_abc_for_midi(cleaned)
    if not ok:
        cleaned = clean_abc_for_midi(
            f"X:1\nM:{default_meter}\nL:1/8\nK:{default_key}\nCDEF GABc |",
            default_key=default_key,
            default_meter=default_meter,
        )
        ok, err = validate_abc_for_midi(cleaned)

    parses, parse_err = verify_abc_parses(cleaned)
    if not parses:
        logger.warning("ABC parse failed (%s) — applying fallback melody", parse_err)
        cleaned = clean_abc_for_midi(
            f"X:1\nT:Studio\nM:{default_meter}\nL:1/8\nK:{default_key}\n"
            f"C2 D2 E2 F2 | G2 A2 B2 c2 |",
            default_key=default_key,
            default_meter=default_meter,
        )
        parses, parse_err = verify_abc_parses(cleaned)
        if not parses:
            return cleaned, False, parse_err or err

    return cleaned, True, None
