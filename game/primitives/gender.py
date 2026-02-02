from __future__ import annotations

from typing import Final

StringAliases = tuple[str, ...]

def _normalize(name: str) -> str:
    # case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    return " ".join(name.strip().lower().split())

_BASE: Final[dict[int, StringAliases]] = {
    -1: ("unspecified", "unknown", "none"),
    0: ("solo", "asexual"),
    1: ("female", "f"),
    2: ("male", "m"),
    3: ("neuter", "n"),
    4: ("egg donor", "egg-donor", "donor"),
    5: ("activator",),
    6: ("bearer",),
    7: ("alt four", "four", "alt 4", "4"),
    8: ("alt five", "five", "alt 5", "5"),
    9: ("alt six", "six", "alt 6", "6"),
    10: ("bizarre",)
}