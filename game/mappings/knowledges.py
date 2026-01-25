from __future__ import annotations

from game.mappings import (
    KNOWLEDGES_BASE_KNOWLEDGE_CODES,
    KNOWLEDGES_FULL_CODE_TO_STR_ALIASES,
)
from game.mappings.attributebase import AttributeBase
from game.mappings.data import (
    AliasMappedFullCodeCollection,
    CanonicalCodeInt,
    MutabilityLevel,
    StringAliases,
)


class Knowledges(AttributeBase):

    __slots__ = (
        "master_knowledge_code_name_aliases_dict",
        "master_focus_code_name_aliases_dict",
    )
    
    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.master_knowledge_code_name_aliases_dict
            self.master_focus_code_name_aliases_dict
        except AttributeError:
            object.__setattr__(self, "master_knowledge_code_name_aliases_dict", dict[CanonicalCodeInt, StringAliases]())
            object.__setattr__(self, "master_focus_code_name_aliases_dict", dict[CanonicalCodeInt, StringAliases]())
        
        super().__init__()

    
    def _initialise_defaults(self) -> None:
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=KNOWLEDGES_FULL_CODE_TO_STR_ALIASES,
            mutability=MutabilityLevel.DEFAULT,
        )
        self.master_knowledge_code_name_aliases_dict.update(KNOWLEDGES_BASE_KNOWLEDGE_CODES)

    