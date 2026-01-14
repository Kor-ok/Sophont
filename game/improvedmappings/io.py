from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, Union

from game.improvedmappings.skills import FullSkillCode, SkillSet

CUSTOM_SKILLS_SCHEMA_VERSION: Final[int] = 1


def _to_jsonable_custom_skills(
    custom: Mapping[str, FullSkillCode],
) -> dict[str, list[int]]:
    """Convert internal custom mapping to a JSON-safe representation."""
    out: dict[str, list[int]] = {}
    for name, code in custom.items():
        master, sub, base = code
        out[str(name)] = [int(master), int(sub), int(base)]
    return out


def save_custom_skills_json(
    path: Union[str, Path],
    skills: Union[SkillSet, Mapping[str, FullSkillCode]],
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
                            }
    }
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    custom_mapping: Mapping[str, FullSkillCode]
    if isinstance(skills, SkillSet):
        custom_mapping = skills.custom_skill_name_to_codes
    else:
        custom_mapping = skills

    payload: dict[str, Any] = {
        "schema": CUSTOM_SKILLS_SCHEMA_VERSION,
        "custom_skills": _to_jsonable_custom_skills(custom_mapping),
    }

    out_path.write_text(json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8")
    return out_path
