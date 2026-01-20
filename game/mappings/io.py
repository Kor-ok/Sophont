from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, Union

from game.mappings.deprecated.attributes import FullCode, StringAliases
from game.mappings.set import AttributesSet
from game.mappings.skills import Skills

CUSTOM_SKILLS_SCHEMA_VERSION: Final[int] = 1


def _to_jsonable_custom_skills(
    custom: Mapping[str, FullCode],
) -> dict[str, list[int]]:
    """Convert custom skills mapping to a JSON-serializable representation.

    `SkillSet.custom_skill_name_to_codes` is a mapping of normalized alias -> full skill code.
    """
    out: dict[str, list[int]] = {}
    for alias, code in custom.items():
        master, sub, base = code
        out[alias] = [int(master), int(sub), int(base)]
    return out


def _to_jsonable_custom_category_dicts(
    custom: Mapping[int, StringAliases],
) -> dict[str, list[str]]:
    """Convert custom category mapping to a JSON-serializable representation."""
    out: dict[str, list[str]] = {}
    for code, names in custom.items():
        out[str(int(code))] = list(names)
    return out


def save_custom_skills_json(
    path: Union[str, Path],
    skills: Union[AttributesSet, Mapping[str, FullCode]],
    master_categories: Union[Mapping[int, StringAliases], None] = None,
    sub_categories: Union[Mapping[int, StringAliases], None] = None,
    *,
    indent: int = 2,
) -> Path:
    """Save custom skills to disk as JSON.

    PLACEHOLDER IMPLEMENTATION

    JSON format (schema v1):
    {
                            "schema": 1,
                            "custom_skills": {
                                            "normalized alias": [master_cat, sub_cat, base_code]
                            },
                            "custom_master_categories": {
                                            master_cat_code: ["alias1", "alias2", ...]
                            },
                            "custom_sub_categories": {
                                            sub_cat_code: ["alias1", "alias2", ...]
                            }
    }
    """
    
    return Path(NotImplemented)
