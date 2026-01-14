from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, Union

from game.improvedmappings.io import save_custom_skills_json
from game.improvedmappings.skills import SKILLS

print("\033c", end="")

# skill_name = "driver"
# full_skill_codes, aliases = SKILLS.resolve(skill_name)

# print(f"Full skill codes for '{skill_name}': {full_skill_codes}")
# print(f"Aliases for '{skill_name}': {aliases}")

custom_skill_name = ("Archeological Accounting",)
master_category_name = ("new master category",)
sub_category_name = ("new sub category",)

message = SKILLS.register_custom_skill(
    skill_name=custom_skill_name,
    master_category_name=master_category_name,
    sub_category_name=sub_category_name,
)

print(message)

# Verify registration
full_skill_codes, aliases = SKILLS.resolve(custom_skill_name[0])
print(f"Full skill codes for '{custom_skill_name[0]}': {full_skill_codes}")
print(f"Aliases for '{custom_skill_name[0]}': {aliases}")

print("\n\n")

# Save to JSON
output_path = "test_custom_skills.json"

save_custom_skills_json(
    path=output_path,
    skills=SKILLS,
)