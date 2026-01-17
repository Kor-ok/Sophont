from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from game.improvedmappings.attributes import AttributesBase
from game.improvedmappings.knowledge_tables import _BASE_KNOWLEDGE_CODES
from game.improvedmappings.utils import _normalize

StringAliases = tuple[str, ...]

BaseKnowledgeInt = int
AssociatedSkillInt = int
FocusInt = int
FullKnowledgeCode = tuple[BaseKnowledgeInt, AssociatedSkillInt, FocusInt]  # (base_knowledge_code, associated_skill_code, focus_code)

CanonicalAlias = str


_UNDEFINED_FULL_KNOWLEDGE_CODE: Final[FullKnowledgeCode] = (-99, -99, -99)


class Knowledges(AttributesBase):

    __slots__ = (
        "custom_knowledge_code_dict",
        "custom_focus_code_dict",
    )
    
    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "custom_knowledge_code_dict", dict[int, StringAliases]())
        object.__setattr__(self, "custom_focus_code_dict", dict[int, StringAliases]())
    
    @property
    def focus_name_to_code(self) -> Mapping[CanonicalAlias, int]:
        """Mapping of normalized focus alias to focus code."""
        out: dict[CanonicalAlias, int] = {}
        for code, aliases in self.custom_focus_code_dict.items():
            for alias in aliases:
                norm_alias = _normalize(alias)
                out[norm_alias] = int(code)
        return MappingProxyType(out)

    def _initialise_defaults(self) -> None:
        """Populate the default knowledges from `knowledge_tables._BASE_KNOWLEDGE_CODES`.
        
        This runs once per process. It intentionally builds a dict and then exposes it read-only.
        """
        default_map: dict[CanonicalAlias, FullKnowledgeCode] = cast(
            dict[CanonicalAlias, FullKnowledgeCode],
            self.default_canonical_alias_key_to_code,
        )

        for BaseKnowledgeInt, (name_aliases, AssociatedSkillInt, FocusInt) in _BASE_KNOWLEDGE_CODES.items():
            full_knowledge_code: FullKnowledgeCode = (
                int(BaseKnowledgeInt),
                int(AssociatedSkillInt),
                int(FocusInt),
            )
            for alias in name_aliases:
                norm_name = _normalize(alias)
                default_map[norm_name] = full_knowledge_code