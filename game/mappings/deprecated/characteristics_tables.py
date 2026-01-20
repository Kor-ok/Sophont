from __future__ import annotations

from dataclasses import dataclass  # Note: Using Python 3.9
from typing import Final

UppPositionInt = int
SubtypeInt = int
MasterCategoryInt = int
CharacteristicIdentifier = tuple[UppPositionInt, SubtypeInt, MasterCategoryInt]
StringAliases = tuple[str, ...]


@dataclass(frozen=True)
class SubtypeDef:
    code: SubtypeInt
    aliases: StringAliases


@dataclass(frozen=True)
class CharacteristicDef:
    upp: UppPositionInt
    master_category: MasterCategoryInt
    aliases: StringAliases
    subtypes: tuple[SubtypeDef, ...] = ()


MASTER_CATEGORIES: Final[dict[int, StringAliases]] = {
    -99: ("undefined",),
    1: ("physical",),
    2: ("mental",),
    3: ("social",),
    4: ("obscure",),
}

CHARACTERISTICS: Final[tuple[CharacteristicDef, ...]] = (
    CharacteristicDef(1, 1, ("strength", "str")),
    CharacteristicDef(2, 1, ("dexterity", "dex"),
        subtypes=(
            SubtypeDef(1, ("agility", "agi")),
            SubtypeDef(2, ("grace", "gra")),
        ),
    ),
    CharacteristicDef(3, 1, ("endurance", "end"),
        subtypes=(
            SubtypeDef(1, ("vigour", "vigor", "vig")),
            SubtypeDef(2, ("stamina", "sta")),
        ),
    ),
    CharacteristicDef(4, 2, ("intelligence", "intellect", "int")),
    CharacteristicDef(5, 2, ("education", "edu"),
        subtypes=(
            SubtypeDef(1, ("training", "tra")),
            SubtypeDef(2, ("instinct", "ins")),
        ),
    ),
    CharacteristicDef(6, 3, ("social standing", "social", "soc"),
        subtypes=(
            SubtypeDef(1, ("charisma", "cha")),
            SubtypeDef(2, ("caste", "cas")),
        ),
    ),
    CharacteristicDef(7, 4, ("psionics", "psi")),
    CharacteristicDef(8, 4, ("sanity", "san")),
)

_BASE_CHARACTERISTIC_CODES: dict[int, StringAliases] = {}
_SUBTYPES_BY_STR: dict[int, tuple[str, ...]] = {}
_SUBTYPES_BY_INT: dict[int, tuple[int, ...]] = {}
_SUBTYPE_ALIASES: dict[str, StringAliases] = {}
_BASE_CODE_TO_CATEGORY_CODE: dict[int, int] = {}
_BASE_CHAR_NAME_TO_CATEGORY_CODE: dict[str, int] = {}

for c in CHARACTERISTICS:
    _BASE_CHARACTERISTIC_CODES[c.upp] = c.aliases
    _BASE_CODE_TO_CATEGORY_CODE[c.upp] = c.master_category
    _BASE_CHAR_NAME_TO_CATEGORY_CODE[c.aliases[0]] = c.master_category

    if c.subtypes:
        subtype_names = tuple(st.aliases[0] for st in c.subtypes)
        _SUBTYPES_BY_STR[c.upp] = subtype_names
        _SUBTYPES_BY_INT[c.upp] = tuple(st.code for st in c.subtypes)

        # Build alias map so short names behave like canonical names
        for st in c.subtypes:
            canonical = st.aliases[0]
            for alias in st.aliases[1:]:
                _SUBTYPE_ALIASES[alias] = (canonical,)