"""Read FIR design parameters from the shared C configuration header."""

import re
from pathlib import Path


HEADER_PATH = Path(__file__).resolve().parents[1] / "c" / "fir_common.h"


def _read_integer_macro(name: str) -> int:
    header = HEADER_PATH.read_text(encoding="utf-8")
    match = re.search(rf"^#define {re.escape(name)} ([0-9]+)$", header, re.MULTILINE)
    if match is None:
        raise ValueError(f"Missing integer macro {name} in {HEADER_PATH}")
    return int(match.group(1))


SAMPLE_RATE_HZ = _read_integer_macro("FIR_SAMPLE_RATE_HZ")
CUTOFF_HZ = _read_integer_macro("FIR_CUTOFF_HZ")
TAP_COUNT = _read_integer_macro("FIR_TAP_COUNT")
