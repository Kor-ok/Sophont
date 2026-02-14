from __future__ import annotations

import re
from typing import Any

from colorama import Fore, Style

"""
This is more of a learning excercise than anything important.
"""


class GlobalState:
    """A singleton class to hold global state variables that can be accessed and modified across the module."""

    __slots__ = ("WIDTH", "CHAR", "COLOUR", "STYLE")

    _instance: GlobalState | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> GlobalState:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Set default values for the global state variables
            cls._instance.WIDTH = 75
            cls._instance.CHAR = "━"
            cls._instance.COLOUR = Fore.WHITE
            cls._instance.STYLE = Style.NORMAL
        return cls._instance

    @classmethod
    def instance(cls) -> GlobalState:
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def divider(
    width: int | None = None,
    char: str | None = None,
    colour: str | None = None,
    style: str | None = None,
) -> None:
    """Print a divider line of the specified length.

    Any non-None argument updates the persistent global state; None leaves the
    existing value unchanged for subsequent calls.
    """
    gs = GlobalState.instance()
    for key, value in {"WIDTH": width, "CHAR": char, "COLOUR": colour, "STYLE": style}.items():
        if value is not None:
            setattr(gs, key, value)

    print(f"{gs.COLOUR}{gs.STYLE}{gs.CHAR * gs.WIDTH}{Style.RESET_ALL}")


def header(
    text: str,
    with_divider: bool = True,
    width: int | None = None,
    char: str | None = None,
    colour: str | None = None,
    style: str | None = None,
) -> None:
    """Print a header using values from the persistent global state.

    Passing non-None values updates the persistent state for later calls.
    """
    gs = GlobalState.instance()
    for key, value in {"WIDTH": width, "CHAR": char, "COLOUR": colour, "STYLE": style}.items():
        if value is not None:
            setattr(gs, key, value)

    text_length = len(text)
    total_length = text_length + 4  # Add padding of 2 spaces on each side
    # Calculate the number of characters needed on each side
    side_length = max((gs.WIDTH - total_length) // 2, 0)
    # Create the header line
    if with_divider:
        header_line = f"{gs.CHAR * side_length}  {text}  {gs.CHAR * side_length}"
    else:
        header_line = f"{'‎' * side_length}  {text}  {'‎' * side_length}"
    # If the total length is odd, add one more character to the end
    if len(header_line) < gs.WIDTH:
        header_line += gs.CHAR if with_divider else "‎"
    print(f"{gs.COLOUR}{gs.STYLE}{header_line}{Style.RESET_ALL}")


def highlight(text: str, colour: str) -> None:
    """Print the given text such that...

    As a foundation we start with Style.DIM, then:
        - Any encapsulated groups (parentheses, brackets, braces, or quoted
          strings) should be Style.NORMAL.  An identifier immediately before
          an opening delimiter is included in the group.
            - Within a group, any integers should be Style.BRIGHT.
        - Standalone integers (outside groups) should also be Style.BRIGHT.
        - If the text contains a top-level ': ' (colon-space not inside a
          group or quotes), everything after the *last* such separator is
          entirely Style.BRIGHT.

    Finally print with the given colour.
    """

    integer_re = re.compile(r"\b\d+\b")

    # -- inner helpers ---------------------------------------------------

    def find_balanced_close(s: str, start: int) -> int:
        """Index of the closing delimiter that balances s[start]."""
        openers = {"(": ")", "[": "]", "{": "}"}
        stack: list[str] = []
        i = start
        while i < len(s):
            ch = s[i]
            if ch in openers:
                stack.append(openers[ch])
            elif ch in (")", "]", "}"):
                if stack and stack[-1] == ch:
                    stack.pop()
                    if not stack:
                        return i
                else:
                    return i  # mismatch — bail
            elif ch in ("'", '"'):
                q = ch
                i += 1
                while i < len(s) and s[i] != q:
                    i += 1
            i += 1
        return len(s) - 1  # unmatched — return end

    def last_top_level_colon(s: str) -> int:
        """Index of the last ': ' not inside delimiters or quotes, or -1."""
        depth = 0
        in_quote: str | None = None
        last = -1
        for i, ch in enumerate(s):
            if in_quote is not None:
                if ch == in_quote:
                    in_quote = None
                continue
            if ch in ("'", '"'):
                in_quote = ch
                continue
            if ch in ("(", "[", "{"):
                depth += 1
            elif ch in (")", "]", "}"):
                depth = max(0, depth - 1)
            elif ch == ":" and depth == 0 and i + 1 < len(s) and s[i + 1] == " ":
                last = i
        return last

    def style_segment(segment: str) -> str:
        """Apply NORMAL/BRIGHT styling to groups, quotes, and integers in
        the prefix portion (everything before the colon separator)."""
        result: list[str] = []
        buf: list[str] = []  # accumulates plain (DIM) characters
        idx = 0
        n = len(segment)

        def flush_plain() -> None:
            if not buf:
                return
            plain = "".join(buf)
            buf.clear()
            # Highlight standalone integers in plain (DIM) text
            result.append(
                integer_re.sub(
                    lambda m: f"{Style.BRIGHT}{m.group(0)}{Style.DIM}",
                    plain,
                )
            )

        while idx < n:
            ch = segment[idx]

            # ---- quoted string ----------------------------------------
            if ch in ("'", '"'):
                flush_plain()
                q = ch
                j = idx + 1
                while j < n and segment[j] != q:
                    j += 1
                if j < n:
                    j += 1  # include closing quote
                group = segment[idx:j]
                styled = integer_re.sub(
                    lambda m: f"{Style.BRIGHT}{m.group(0)}{Style.NORMAL}",
                    group,
                )
                result.append(f"{Style.NORMAL}{styled}{Style.DIM}")
                idx = j
                continue

            # ---- delimiter group (with optional preceding identifier) -
            if ch in ("(", "[", "{"):
                # Pull any preceding identifier out of the plain buffer
                ident_chars: list[str] = []
                while buf and (buf[-1].isalnum() or buf[-1] == "_"):
                    ident_chars.append(buf.pop())
                ident_chars.reverse()
                flush_plain()

                j = find_balanced_close(segment, idx)
                group = "".join(ident_chars) + segment[idx : j + 1]
                styled = integer_re.sub(
                    lambda m: f"{Style.BRIGHT}{m.group(0)}{Style.NORMAL}",
                    group,
                )
                result.append(f"{Style.NORMAL}{styled}{Style.DIM}")
                idx = j + 1
                continue

            # ---- ordinary character -----------------------------------
            buf.append(ch)
            idx += 1

        flush_plain()
        return "".join(result)

    # -- main body -------------------------------------------------------
    colon_pos = last_top_level_colon(text)

    if colon_pos != -1:
        prefix = text[:colon_pos]
        suffix = text[colon_pos + 2 :]  # skip ': '
        styled = f"{style_segment(prefix)}: {Style.BRIGHT}{suffix}"
    else:
        styled = style_segment(text)

    print(f"{colour}{Style.NORMAL}{styled}{Style.RESET_ALL}")


if __name__ == "__main__":
    header(
        "Testing terminal utilities...", width=50, char="=", colour=Fore.CYAN, style=Style.BRIGHT
    )
    divider()
