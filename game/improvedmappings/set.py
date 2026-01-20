from __future__ import annotations

from typing import Final, Optional

from game.improvedmappings.characteristics import Characteristics
from game.improvedmappings.knowledges import Knowledges
from game.improvedmappings.skills import Skills


class AttributesSet:
    """App-wide store for RPG skills, knowleges and future extensions like certifications.

    - Default skills are loaded from `game.improvedmappings.skill_tables` once and then exposed read-only.
    - Default knowledges are loaded from `game.improvedmappings.knowledge_tables._BASE_KNOWLEDGES_CODES`.
    - Custom skills can be registered/removed at runtime.
    - Custom knowledges can be registered/removed at runtime.
    - Custom master and sub category code tables can be extended/culled at runtime.
    - Focus Codes are dict[int, StringAliases], defined entirely at runtime and
        refer to things like language names, or world names, etc.
    - Lookups are normalized (`casefold` + collapsed whitespace).

    This is implemented as a singleton so all callers share the same store:

        aptitudes = AptitudesSet()  # always returns the same instance
    """

    __slots__ = (
        "skills",
        "knowledges",
        "characteristics",
        "_is_initialised",
    )

    _instance: Optional[AttributesSet] = None

    def __new__(cls) -> AttributesSet:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "skills", Skills())
        object.__setattr__(self, "knowledges", Knowledges())
        object.__setattr__(self, "characteristics", Characteristics())

        object.__setattr__(self, "_is_initialised", False)

        cls._instance = self
        return self

    def __init__(self) -> None:
        if self._is_initialised:
            return
        object.__setattr__(self, "_is_initialised", True)

    def get_skill(self, name: str):
        """Get a skill by name."""
        return self.skills.resolve_skill(name)
    
    def get_all_skills(self):
        """Get all defined skills as (full_skill_code, aliases) tuples."""
        all_skills = []
        for norm_name, full_skill_code in self.skills.combined_view.items():
            aliases = self.skills._return_string_code_names(full_skill_code)
            all_skills.append((full_skill_code, aliases))
        return all_skills

    def get_knowledge(self, name: str):
        """Get a knowledge by name."""
        return self.knowledges.resolve_knowledge(name)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"skills={repr(self.skills)}, "
            f"knowledges={repr(self.knowledges)}, "
            f"characteristics={repr(self.characteristics)})"
        )


# Convenience singleton instance for app-wide usage.
ATTRIBUTES: Final[AttributesSet] = AttributesSet()
