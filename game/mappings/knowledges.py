from __future__ import annotations

from game.mappings import KNOWLEDGES_FULL_CODE_TO_STR_ALIASES
from game.mappings.attributebase import AttributeBase
from game.mappings.data import AliasMappedFullCodeCollection, MutabilityLevel

StringAliases = tuple[str, ...]
CodeNames = tuple[str, ...]

BaseKnowledgeInt = int
AssociatedSkillInt = int
FocusInt = int
FullKnowledgeCode = tuple[BaseKnowledgeInt, AssociatedSkillInt, FocusInt]  # (base_knowledge_code, associated_skill_code, focus_code)

AssociatedSkillCodes = tuple[int, ...]

CanonicalAlias = str


class Knowledges(AttributeBase):

    __slots__ = (
        "custom_knowledge_code_name_aliases_dict",
        "custom_focus_code_name_aliases_dict",
    )
    
    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.custom_knowledge_code_name_aliases_dict
            self.custom_focus_code_name_aliases_dict
        except AttributeError:
            object.__setattr__(self, "custom_knowledge_code_name_aliases_dict", dict[int, StringAliases]())
            object.__setattr__(self, "custom_focus_code_name_aliases_dict", dict[int, StringAliases]())
        
        super().__init__()

    
    def _initialise_defaults(self) -> None:
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=KNOWLEDGES_FULL_CODE_TO_STR_ALIASES,
            mutability=MutabilityLevel.DEFAULT,
        )

    