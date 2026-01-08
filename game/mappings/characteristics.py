from __future__ import annotations

from typing import Final

CharacteristicIdentifier = tuple[int, int]  # position_code, subtype_code
StringAliases = tuple[str, ...]

"""mappings.characteristics

Representation used throughout the codebase:
- Base characteristic position codes are 1-based (1..8)
- Subtype codes are 0-based for "base" (no subtype)
    and 1..N for subtypes of that base characteristic.

This avoids a collision where both "base" and the first subtype would otherwise be 0.
"""

def _normalize(name: str) -> str:
    # case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    return " ".join(name.strip().lower().split())


# Base characteristics: any of these names map to (position_code, subtype_code=0)
_BASE: Final[dict[int, StringAliases]] = {
    1: ("strength", "str"),
    2: ("dexterity", "dex"),
    3: ("endurance", "end"),
    4: ("intelligence", "intellect", "int"),
    5: ("education", "edu"),
    6: ("social standing", "social", "soc"),
    7: ("psionics", "psi"),
    8: ("sanity", "san"),
}

# Subtypes by position_code; subtype_code is 1-based (1..N)
_SUBTYPES: Final[dict[int, StringAliases]] = {
    2: ("agility", "grace"),
    3: ("vigour", "stamina"),
    5: ("training", "instinct"),
    6: ("charisma", "caste"),
}

# Short aliases that should behave exactly like their canonical subtype name
_SUBTYPE_ALIASES: Final[dict[str, StringAliases]] = {
    "agi": ("agility",),
    "gra": ("grace",),
    "vig": ("vigour", "vigor"),  # handle both spellings
    "sta": ("stamina",),
    "tra": ("training",),
    "ins": ("instinct",),
    "cha": ("charisma",),
    "cas": ("caste",),
}


# Build a single lookup: normalized name -> (position_code, subtype_code)
_NAME_TO_CODES: dict[str, CharacteristicIdentifier] = {}

for pos_code, names in _BASE.items():
    for n in names:
        _NAME_TO_CODES[_normalize(n)] = (pos_code, 0)

for pos_code, subtype_names in _SUBTYPES.items():
    for sub_code, canonical in enumerate(subtype_names):
        _NAME_TO_CODES[_normalize(canonical)] = (pos_code, sub_code + 1)

# Add alias entries.
#
# Important: `Final[...]` is a *typing* hint only (for linters/type checkers).
# It does not freeze or speed up the dict at runtime.
# The runtime wins here come from:
#   - building a single dict `_NAME_TO_CODES` once at import time
#   - doing O(1) dict lookups at runtime (instead of scanning lists)
#   - avoiding extra string work on hot paths
for alias, canonical in _SUBTYPE_ALIASES.items():
    resolved_code: CharacteristicIdentifier | None = None
    for canonical_name in canonical:
        canonical_key = _normalize(canonical_name)
        code = _NAME_TO_CODES.get(canonical_key)
        if code is not None:
            resolved_code = code
            break

    if resolved_code is None:
        continue

    # Alias token itself (e.g. "vig")
    _NAME_TO_CODES[_normalize(alias)] = resolved_code
    # Also register alternate spellings/synonyms listed under that alias (e.g. "vigor").
    for canonical_name in canonical:
        _NAME_TO_CODES[_normalize(canonical_name)] = resolved_code

def name_to_position_code(name: str) -> CharacteristicIdentifier:
    # Hot path: do one normalization and one dict lookup.
    # We already expanded aliases/alternate spellings into `_NAME_TO_CODES`.
    key = _normalize(name)
    return _NAME_TO_CODES.get(key, (-1, -1))

# Position Code and Subtype Code to Name
def codes_to_name(pos_code: int, sub_code: int = 0) -> str:
    # Keep lookups branch-light: one .get() instead of "in" + indexing.
    subtype_names = _SUBTYPES.get(pos_code)
    if subtype_names is not None and sub_code > 0:
        subtype_index = sub_code - 1
        if 0 <= subtype_index < len(subtype_names):
            return subtype_names[subtype_index].title()

    base_names = _BASE.get(pos_code)
    if base_names is not None:
        return base_names[0].title()
    return "Undefined"

_CATEGORY_MAP: Final[dict[int, str]] = {
    0: "Undefined",
    1: "Physical",
    2: "Mental",
    3: "Social",
    4: "Obscure",
}

_BASE_CHAR_NAME_TO_CATEGORY_CODE: Final[dict[str, int]] = {
    "strength": 1,
    "dexterity": 1,
    "endurance": 1,
    "intelligence": 2,
    "education": 2,
    "social standing": 3,
    "psionics": 4,
    "sanity": 4,
}

_BASE_CODE_TO_CATEGORY_CODE: Final[dict[int, int]] = {
    1: 1,  # Strength -> Physical
    2: 1,  # Dexterity -> Physical
    3: 1,  # Endurance -> Physical
    4: 2,  # Intelligence -> Mental
    5: 2,  # Education -> Mental
    6: 3,  # Social Standing -> Social
    7: 4,  # Psionics -> Obscure
    8: 4,  # Sanity -> Obscure
}

# check alias convenience function
def _check_alias(pos_code: int) -> str:
    if pos_code in _BASE:
        base_names = _BASE[pos_code]
        canonical_name = base_names[0]
        return _normalize(canonical_name)
    return "Undefined"

# lookup: normalized name -> (category_code)
_CHAR_NAME_TO_CATEGORY_CODE: dict[str, int] = {}
for name, cat_code in _BASE_CHAR_NAME_TO_CATEGORY_CODE.items():
    _CHAR_NAME_TO_CATEGORY_CODE[_normalize(name)] = cat_code

def char_name_to_category_code(name: str) -> int:
    key = _normalize(name)
    # Also check for alias like if "intellect" is given instead of "intelligence"
    if key not in _CHAR_NAME_TO_CATEGORY_CODE:
        pos_code, _ = name_to_position_code(name)
        key = _check_alias(pos_code)
    return _CHAR_NAME_TO_CATEGORY_CODE.get(key, 0)

# Category Code to Category Name Convenience
def category_code_to_category_name(cat_code: int) -> str:
    return _CATEGORY_MAP.get(cat_code, "Undefined")

