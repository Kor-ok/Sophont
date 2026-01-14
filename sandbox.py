from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, Union

from game.improvedmappings.skills import SKILLS

skill_name = "driver"
full_skill_codes, aliases = SKILLS.resolve(skill_name)

print(f"Full skill codes for '{skill_name}': {full_skill_codes}")
print(f"Aliases for '{skill_name}': {aliases}")