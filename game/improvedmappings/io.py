from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, Union

from game.improvedmappings.attributes import FullCode, StringAliases
from game.improvedmappings.set import AttributesSet
from game.improvedmappings.skills import Skills

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
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    custom_mapping: Mapping[str, FullCode]
    custom_master_categories: Mapping[int, StringAliases]
    custom_sub_categories: Mapping[int, StringAliases]

    if isinstance(skills, AttributesSet):
        custom_mapping = Skills.custom_skill_code_dict
        custom_master_categories = Skills.custom_master_category_dict
        custom_sub_categories = Skills.custom_sub_category_dict
    else:
        custom_mapping = {}
        custom_master_categories = master_categories or {}
        custom_sub_categories = sub_categories or {}

    payload: dict[str, Any] = {
        "schema": CUSTOM_SKILLS_SCHEMA_VERSION,
        "custom_skills": _to_jsonable_custom_skills(custom_mapping),
        "custom_master_categories": _to_jsonable_custom_category_dicts(custom_master_categories),
        "custom_sub_categories": _to_jsonable_custom_category_dicts(custom_sub_categories),
    }

    chars_written = out_path.write_text(
        json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8"
    )
    print(f"{chars_written} chars - Custom skills saved to: {out_path.resolve()}")
    return out_path
