from __future__ import annotations

from functools import lru_cache
from typing import Final, Optional, Dict, Tuple, List
from enum import Enum

from game.mappings.skill_tables import _BASE, _MASTER_CAT, _SUB_CAT, _KNOWLEDGES, _BASE_SKILL_CODE_TO_CATEGORIES

class Table(Enum):
    BASE = "base_skills"
    MASTER_CATEGORY = "master_skill_categories"
    SUB_CATEGORY = "sub_skill_categories"
    KNOWLEDGES = "knowledges"

@lru_cache(maxsize=4096)
def _normalize(name: str) -> str:
    # case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    return " ".join(name.strip().casefold().split())

def _insert_context(raw_string: str, context: str) -> str:
    if "<name>" in raw_string:
        return raw_string.replace("<name>", context)
    return raw_string

# ================================================ BASE SKILLS ================================================ #
    
StringAliases = Tuple[str, ...]

def _build_dense_primary_name_table(table: Dict[int, StringAliases], default: str = "undefined") -> tuple[int, tuple[str, ...]]:
    """Build (min_code, dense_tuple) where dense_tuple[code-min_code] is primary name."""
    min_code = min(table.keys(), default=-99)
    max_code = max(table.keys(), default=-99)
    dense = [default] * (max_code - min_code + 1)
    for code, aliases in table.items():
        dense[code - min_code] = aliases[0]
    return min_code, tuple(dense)

def _dense_get(code: int, min_code: int, dense: tuple[str, ...], default: str = "undefined") -> str:
    idx = code - min_code
    if 0 <= idx < len(dense):
        return dense[idx]
    return default

_MIN_BASE_CODE: Final[int]
_BASE_PRIMARY_BY_CODE: Final[tuple[str, ...]]
_MIN_BASE_CODE, _BASE_PRIMARY_BY_CODE = _build_dense_primary_name_table(_BASE)

def _base_primary_name(code: int) -> str:
    return _dense_get(code, _MIN_BASE_CODE, _BASE_PRIMARY_BY_CODE)

def _build_norm_alias_lookup(table: Dict[int, StringAliases]) -> Dict[str, int]:
    lookup: Dict[str, int] = {}
    for code, aliases in table.items():
        for alias in aliases:
            lookup[_normalize(alias)] = code
    return lookup

_NORM_BASE_NAME_TO_CODE: Final[Dict[str, int]] = _build_norm_alias_lookup(_BASE)

# ================================================ MASTER CATEGORY ================================================ #

_MIN_MASTER_CAT_CODE: Final[int] = min(_MASTER_CAT.keys(), default=-99)
_MAX_MASTER_CAT_CODE: Final[int] = max(_MASTER_CAT.keys(), default=-99)
_MASTER_CAT_BY_CODE: Final[tuple[str, ...]] = tuple(
    _MASTER_CAT.get(code, "undefined") for code in range(_MIN_MASTER_CAT_CODE, _MAX_MASTER_CAT_CODE + 1)
)

def _master_category_name(code: int) -> str:
    return _dense_get(code, _MIN_MASTER_CAT_CODE, _MASTER_CAT_BY_CODE)

_NORM_MASTER_CATEGORY_NAME_TO_CODE: Final[dict[str, int]] = {
    _normalize(cat_name): code for code, cat_name in _MASTER_CAT.items()
}

# ================================================ SUB CATEGORY ================================================ #

_MIN_SUB_CAT_CODE: Final[int] = min(_SUB_CAT.keys(), default=-99)
_MAX_SUB_CAT_CODE: Final[int] = max(_SUB_CAT.keys(), default=-99)
_SUB_CAT_BY_CODE: Final[tuple[str, ...]] = tuple(
    _SUB_CAT.get(code, "undefined") for code in range(_MIN_SUB_CAT_CODE, _MAX_SUB_CAT_CODE + 1)
)

def _sub_category_name(code: int) -> str:
    return _dense_get(code, _MIN_SUB_CAT_CODE, _SUB_CAT_BY_CODE)

_NORM_SUB_CATEGORY_NAME_TO_CODE: Final[dict[str, int]] = {
    _normalize(cat_name): code for code, cat_name in _SUB_CAT.items()
}

# ================================================ KNOWLEDGES ================================================ #

_MIN_KNOWLEDGE_CODE: Final[int]
_KNOWLEDGE_PRIMARY_BY_CODE: Final[tuple[str, ...]]
_MIN_KNOWLEDGE_CODE, _KNOWLEDGE_PRIMARY_BY_CODE = _build_dense_primary_name_table(_KNOWLEDGES)

def _knowledge_primary_name(code: int) -> str:
    return _dense_get(code, _MIN_KNOWLEDGE_CODE, _KNOWLEDGE_PRIMARY_BY_CODE)

_NORM_KNOWLEDGE_NAME_TO_CODE: Final[Dict[str, int]] = _build_norm_alias_lookup(_KNOWLEDGES)

# ================================================ CATEGORY MAPPINGS ================================================ #

# Integer based mapping of which master and sub categories apply to each skill code.
# Format: skill_code: (master_category_code, sub_category_code)
SkillCode = int
CategoryCodesTuple = Tuple[int, int]

_UNDEFINED_CATEGORIES: Final[CategoryCodesTuple] = (-99, -99)
_MIN_SKILL_CODE: Final[int] = min(_BASE_SKILL_CODE_TO_CATEGORIES.keys(), default=-99)
_MAX_SKILL_CODE: Final[int] = max(_BASE_SKILL_CODE_TO_CATEGORIES.keys(), default=-99)
_CATEGORY_BY_SKILL_CODE_LIST: List[CategoryCodesTuple] = [_UNDEFINED_CATEGORIES] * (
    _MAX_SKILL_CODE - _MIN_SKILL_CODE + 1
)
for _code, _cats in _BASE_SKILL_CODE_TO_CATEGORIES.items():
    _CATEGORY_BY_SKILL_CODE_LIST[_code - _MIN_SKILL_CODE] = _cats
_CATEGORY_BY_SKILL_CODE: Final[tuple[CategoryCodesTuple, ...]] = tuple(_CATEGORY_BY_SKILL_CODE_LIST)
del _CATEGORY_BY_SKILL_CODE_LIST

# ================================================ API ================================================ #

def code_to_string(code: int, table: Table, context: Optional[str] = None, capitalise: bool = False) -> str:
    cap = (str.title if capitalise else (lambda s: s))

    if table is Table.BASE:
        return cap(_base_primary_name(code))
    if table is Table.KNOWLEDGES:
        raw = _knowledge_primary_name(code)
        return cap(_insert_context(raw, context) if context else raw)
    if table is Table.MASTER_CATEGORY:
        return cap(_master_category_name(code))
    if table is Table.SUB_CATEGORY:
        return cap(_sub_category_name(code))
    return cap("undefined")

def get_base_skill_code_from_name(name: str) -> int:
    return _NORM_BASE_NAME_TO_CODE.get(_normalize(name), -99)

def get_master_category_code_from_name(name: str) -> int:
    return _NORM_MASTER_CATEGORY_NAME_TO_CODE.get(_normalize(name), -99)


def get_sub_category_code_from_name(name: str) -> int:
    return _NORM_SUB_CATEGORY_NAME_TO_CODE.get(_normalize(name), -99)

def get_knowledge_code_from_name(name: str, associated_skill: Optional[str] = None) -> int:
    code = _NORM_KNOWLEDGE_NAME_TO_CODE.get(_normalize(name))
    if code is not None:
        return code

    if associated_skill is not None and _normalize(associated_skill) == "language":
        return 66
    
    if associated_skill is not None and _normalize(associated_skill) == "world":
        return 64

    return -99

def get_contexted_knowledge_name_from_code(code: int, context: Optional[str] = None) -> str:
    raw = _KNOWLEDGES.get(code, ("undefined",))[0]
    return (_insert_context(raw, context) if context else raw).title()

def get_category_codes_from_skill_code(skill_code: int) -> CategoryCodesTuple:
    idx = skill_code - _MIN_SKILL_CODE
    if 0 <= idx < len(_CATEGORY_BY_SKILL_CODE):
        return _CATEGORY_BY_SKILL_CODE[idx]
    return _UNDEFINED_CATEGORIES