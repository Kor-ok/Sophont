from __future__ import annotations

from typing import Final, Tuple, Dict, List

CharacteristicIdentifier = Tuple[int, int]  # position_code, subtype_code
StringAliases = Tuple[str, ...]

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
_BASE: Final[Dict[int, StringAliases]] = {
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
_SUBTYPES: Final[Dict[int, StringAliases]] = {
    2: ("agility", "grace"),
    3: ("vigour", "stamina"),
    5: ("training", "instinct"),
    6: ("charisma", "caste"),
}

# Short aliases that should behave exactly like their canonical subtype name
_SUBTYPE_ALIASES: Final[Dict[str, StringAliases]] = {
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
_NAME_TO_CODES: Dict[str, CharacteristicIdentifier] = {}

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

_CATEGORY_MAP: Final[Dict[int, str]] = {
    0: "Undefined",
    1: "Physical",
    2: "Mental",
    3: "Social",
    4: "Obscure",
}

_BASE_CHAR_NAME_TO_CATEGORY_CODE: Final[Dict[str, int]] = {
    "strength": 1,
    "dexterity": 1,
    "endurance": 1,
    "intelligence": 2,
    "education": 2,
    "social standing": 3,
    "psionics": 4,
    "sanity": 4,
}

# check alias convenience function
def _check_alias(pos_code: int) -> str:
    if pos_code in _BASE:
        base_names = _BASE[pos_code]
        canonical_name = base_names[0]
        return _normalize(canonical_name)
    return "Undefined"

# lookup: normalized name -> (category_code)
_CHAR_NAME_TO_CATEGORY_CODE: Dict[str, int] = {}
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

# convenience function to return a genetic profile which is
# a list where index is position_code and value is 
# the first letter of the final name of the characteristic as 
# derived from a list of tuple(position_code, subtype_code)
def codes_to_genetic_profile(code_tuples_list: List[CharacteristicIdentifier]) -> List[str]:
    """
    Generate genetic profile list from position and subtype codes.
    codes: list[tuple[int, int]] = [(char.c_pos, char.c_subtype) for char in sophont.characteristics.collection]
    """
    # O(n): fill a fixed-size list indexed by pos_code.
    # This avoids the nested scan (O(8*n)) in hot paths.
    profile: List[str] = ["*"] * 8
    for pos_code, sub_code in code_tuples_list:
        if 1 <= pos_code <= 8:
            full_name = codes_to_name(pos_code, sub_code)
            profile[pos_code - 1] = full_name[0].upper() if full_name else "*"
    return profile