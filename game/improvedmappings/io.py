from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, Union

from game.improvedmappings.skills import FullSkillCode, SkillSet, StringAliases

CUSTOM_SKILLS_SCHEMA_VERSION: Final[int] = 1


def _to_jsonable_custom_skills(
    custom: Mapping[StringAliases, FullSkillCode],
) -> dict[StringAliases, FullSkillCode]:
    """Convert internal custom mapping to a JSON-safe representation."""
    out: dict[StringAliases, FullSkillCode] = {}
    for name, code in custom.items():
        master, sub, base = code
        out[name] = (master, sub, base)
    return out

def _to_jsonable_custom_category_dicts(
    custom: Mapping[int, StringAliases],
) -> dict[int, StringAliases]:
    """Convert internal custom category mapping to a JSON-safe representation."""
    out: dict[int, StringAliases] = {}
    for code, names in custom.items():
        out[code] = names
    return out
        

def save_custom_skills_json(
    path: Union[str, Path],
    skills: Union[SkillSet, Mapping[str, FullSkillCode]],
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

    custom_mapping: Mapping[StringAliases, FullSkillCode]
    if isinstance(skills, SkillSet):
        custom_mapping = skills.custom_skill_name_to_codes
        custom_master_categories = skills.custom_master_category_dict
        custom_sub_categories = skills.custom_sub_category_dict

    payload: dict[str, Any] = {
        "schema": CUSTOM_SKILLS_SCHEMA_VERSION,
        "custom_skills": _to_jsonable_custom_skills(custom_mapping),
        "custom_master_categories": _to_jsonable_custom_category_dicts(custom_master_categories),
        "custom_sub_categories": _to_jsonable_custom_category_dicts(custom_sub_categories),
    }

    feedback = out_path.write_text(json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8")
    print(f"{feedback} - Custom skills saved to: {out_path.resolve()}")
    return out_path
