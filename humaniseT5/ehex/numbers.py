from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from random import choice
from typing import Optional, Union

"""Traveller 5 Expanded Hex Code (eHex).

eHex represents values 0..33 using 0-9 then A..Z (omitting I and O).

This module also supports a few non-numeric tokens commonly seen in authored data:

- ``TRUE`` / ``FALSE`` (boolean-like tokens)
- ``?`` (unknown)
- ``*`` (any / wildcard)
"""


class EHex(Enum):
    """A robust eHex value.

    - Numeric digits have a defined integer value (0..33) and a canonical token (e.g. ``"7"``, ``"C"``).
    - Special tokens do not have an integer value.

    Use :meth:`parse` / :meth:`from_int` to construct values, and :meth:`token` / :meth:`int_value`
    for formatting and numeric access.
    """

    ZERO = ("0", 0)
    ONE = ("1", 1)
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)

    A = ("A", 10)
    B = ("B", 11)
    C = ("C", 12)
    D = ("D", 13)
    E = ("E", 14)
    F = ("F", 15)
    G = ("G", 16)
    H = ("H", 17)
    J = ("J", 18)
    K = ("K", 19)
    L = ("L", 20)
    M = ("M", 21)
    N = ("N", 22)
    P = ("P", 23)
    Q = ("Q", 24)
    R = ("R", 25)
    S = ("S", 26)
    T = ("T", 27)
    U = ("U", 28)
    V = ("V", 29)
    W = ("W", 30)
    X = ("X", 31)
    Y = ("Y", 32)
    Z = ("Z", 33)

    TRUE = ("TRUE", None)
    FALSE = ("FALSE", None)
    UNKNOWN = ("?", None)
    ANY = ("*", None)

    def __init__(self, token: str, int_value: Optional[int]) -> None:
        self._token = token
        self._int_value = int_value

    @property
    def token(self) -> str:
        """Canonical string token (e.g. ``"A"`` or ``"?"``)."""

        return self._token

    @property
    def int_value(self) -> Optional[int]:
        """Numeric value for digits (0..33), otherwise ``None``."""

        return self._int_value

    @property
    def is_digit(self) -> bool:
        return self._int_value is not None

    def __str__(self) -> str:  # pragma: no cover (tiny convenience)
        return self._token

    def __int__(self) -> int:
        if self._int_value is None:
            raise TypeError(f"{self.name} has no integer value")
        return self._int_value

    @classmethod
    def digits(cls) -> Iterable[EHex]:
        """Iterate numeric eHex digits in ascending order."""

        for member in cls:
            if member.is_digit:
                yield member

    @classmethod
    def from_int(cls, value: int) -> EHex:
        if not isinstance(value, int):
            raise TypeError("value must be an int")
        if value < 0 or value > 33:
            raise ValueError("eHex digit must be in the range 0..33")

        mapping = _INT_TO_EHEX
        try:
            return mapping[value]
        except KeyError as exc:  # pragma: no cover
            raise ValueError(f"No eHex digit for value: {value}") from exc

    @classmethod
    def parse(cls, value: Union[str, int, EHex]) -> EHex:
        """Parse an eHex value from a token or integer.

        Accepted inputs:
        - ``EHex`` (returns as-is)
        - ``int`` (0..33)
        - ``str`` tokens: ``0``..``9``, ``A``..``Z`` (excluding I/O), ``?``, ``*``, ``TRUE``, ``FALSE``
          (case-insensitive; surrounding whitespace ignored)
        """

        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls.from_int(value)
        if not isinstance(value, str):
            raise TypeError("value must be str, int, or EHex")

        text = value.strip()
        if not text:
            raise ValueError("Empty eHex token")

        normalized = text.upper()

        # Allow numeric strings like "10" in addition to single-character tokens.
        if normalized.isdigit():
            return cls.from_int(int(normalized))

        mapping = _TOKEN_TO_EHEX
        try:
            return mapping[normalized]
        except KeyError as exc:
            raise ValueError(f"No eHex representation for token: {value!r}") from exc

    def increment(self, by: int = 1) -> EHex:
        """Return the digit that is ``by`` steps above this one.

        - ``ANY`` and ``UNKNOWN`` are returned unchanged (stable sentinel semantics).
        - For numeric digits, increments within 0..33.
        """

        if self in (EHex.ANY, EHex.UNKNOWN):
            return self
        if not self.is_digit:
            raise ValueError(f"Cannot increment non-numeric eHex value: {self.token}")

        if not isinstance(by, int):
            raise TypeError("by must be an int")

        return EHex.from_int(int(self) + by)

    @classmethod
    def random_digit(cls) -> EHex:
        """Return a random numeric eHex digit."""

        return choice(list(cls.digits()))


_INT_TO_EHEX: dict[int, EHex] = {}
_TOKEN_TO_EHEX: dict[str, EHex] = {}

for _member in EHex:
    if _member.int_value is not None:
        _INT_TO_EHEX[_member.int_value] = _member
    _TOKEN_TO_EHEX[_member.token.upper()] = _member