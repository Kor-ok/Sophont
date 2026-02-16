from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import pandas as pd


@lru_cache(maxsize=100)
def lowercase_and_strip(s: str) -> str:
    """Convert a string to lowercase and strip leading/trailing whitespace."""
    return s.strip().lower()

def convert_type_to_str_name(t: type) -> str:
    """Convert a type object to a string representation, e.g. int -> 'int'."""
    if hasattr(t, "__name__"):
        return t.__name__
    else:
        return str(t)

@lru_cache(maxsize=300)
def convert_comma_delimited_str_to_tuple(s: Any, type: type | None = None) -> tuple[Any, ...]:
    """Convert a comma-delimited string like "1, 0, 1" into a tuple of a sensible type.

    Rules:
    - If `s` is already a tuple/list, return a tuple(s).
    - If `s` is not a string, return a single-element tuple `(s,)`.
    - Ignore empty items produced by consecutive commas or surrounding whitespace.
    - If `type` is provided, coerce every item to that type.
    - If `type` is not provided, infer the most specific common type across all items
      using these checks (in order): all-int -> int, all-float-or-int -> float,
      all-bool -> bool, otherwise str.
    """
    # If Pandas is providing a nan, convert to empty tuple
    if isinstance(s, float) and pd.isna(s):
        return tuple()
    if isinstance(s, (tuple, list)):
        return tuple(s)
    if not isinstance(s, str):
        return (s,)

    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p != ""]
    if not parts:
        return tuple()

    int_re = re.compile(r"^[+-]?\d+$")
    float_re = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+|\d+[eE][+-]?\d+)$")
    bool_vals = {"true", "false", "yes", "no", "1", "0"}

    def is_int(x: str) -> bool:
        return bool(int_re.match(x))

    def is_float(x: str) -> bool:
        return bool(float_re.match(x)) or is_int(x)

    def is_bool(x: str) -> bool:
        return x.lower() in bool_vals

    # If caller provided a type, use it
    if type is not None:
        if type is int:
            return tuple(int(p) for p in parts)
        if type is float:
            return tuple(float(p) for p in parts)
        if type is bool:
            return tuple(p.lower() in ("true", "1", "yes") for p in parts)
        return tuple(p for p in parts)

    # Infer a common type across all parts
    if all(is_int(p) for p in parts):
        return tuple(int(p) for p in parts)
    if all(is_float(p) for p in parts):
        return tuple(float(p) for p in parts)
    if all(is_bool(p) for p in parts):
        return tuple(p.lower() in ("true", "1", "yes") for p in parts)

    return tuple(p for p in parts)
