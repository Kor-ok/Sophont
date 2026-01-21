from __future__ import annotations

from collections.abc import Mapping

from game.mappings import (
    SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
)
from game.mappings.attributebase import AttributeBase
from game.mappings.data import AliasMappedFullCodeCollection, MutabilityLevel

StringAliases = tuple[str, ...]
CanonicalStrKey = str

MasterCategoryInt = int
SubCategoryInt = int
BaseSkillInt = int
FullCode = tuple[MasterCategoryInt, SubCategoryInt, BaseSkillInt]

AliasMap = Mapping[CanonicalStrKey, StringAliases]
AliasMappedFullCode = tuple[AliasMap, FullCode]


class Skills(AttributeBase):
    """Handles populating default skills and managing the mapping of custom skills.
    
    """
    __slots__ = (
        "custom_skill_code_name_aliases_dict",
        "custom_master_category_name_aliases_dict",
        "custom_sub_category_name_aliases_dict",
    )

    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.custom_skill_code_name_aliases_dict
            self.custom_master_category_name_aliases_dict
            self.custom_sub_category_name_aliases_dict
        except AttributeError:
            object.__setattr__(self, "custom_skill_code_name_aliases_dict", dict[int, StringAliases]())
            object.__setattr__(self, "custom_master_category_name_aliases_dict", dict[int, StringAliases]())
            object.__setattr__(self, "custom_sub_category_name_aliases_dict", dict[int, StringAliases]())

        super().__init__()

    def _initialise_defaults(self) -> None:
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
            mutability=MutabilityLevel.DEFAULT,
        )

    