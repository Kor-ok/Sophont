from __future__ import annotations

from game.mappings import (
    SKILLS_BASE_SKILL_CODES,
    SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
    SKILLS_MASTER_CATEGORY_CODES,
    SKILLS_SUB_CATEGORY_CODES,
)
from game.mappings.attributebase import AttributeBase
from game.mappings.data import (
    AliasMappedFullCodeCollection,
    MutabilityLevel,
    StringAliases,
)


class Skills(AttributeBase):
    """Handles populating default skills and managing the mapping of custom skills.
    
    """
    __slots__ = (
        "master_category_name_aliases_dict",
        "master_sub_category_name_aliases_dict",
        "master_skill_code_name_aliases_dict",
    )

    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.master_category_name_aliases_dict
            self.master_sub_category_name_aliases_dict
            self.master_skill_code_name_aliases_dict
        except AttributeError:
            object.__setattr__(self, "master_category_name_aliases_dict", dict[int, StringAliases]())
            object.__setattr__(self, "master_sub_category_name_aliases_dict", dict[int, StringAliases]())
            object.__setattr__(self, "master_skill_code_name_aliases_dict", dict[int, StringAliases]())
        super().__init__()

    def _initialise_defaults(self) -> None:
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
            mutability=MutabilityLevel.DEFAULT,
        )
        self.master_category_name_aliases_dict.update(SKILLS_MASTER_CATEGORY_CODES)
        self.master_sub_category_name_aliases_dict.update(SKILLS_SUB_CATEGORY_CODES)
        self.master_skill_code_name_aliases_dict.update(SKILLS_BASE_SKILL_CODES)
    