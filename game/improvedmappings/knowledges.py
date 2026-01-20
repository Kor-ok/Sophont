from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from game.improvedmappings import (
    KNOWLEDGES_BASE_KNOWLEDGE_CODES,
    KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS,
)
from game.improvedmappings.attributes import AttributesBase
from game.improvedmappings.utils import _normalize

StringAliases = tuple[str, ...]
CodeNames = tuple[str, ...]

BaseKnowledgeInt = int
AssociatedSkillInt = int
FocusInt = int
FullKnowledgeCode = tuple[BaseKnowledgeInt, AssociatedSkillInt, FocusInt]  # (base_knowledge_code, associated_skill_code, focus_code)

AssociatedSkillCodes = tuple[int, ...]

CanonicalAlias = str


_UNDEFINED_FULL_KNOWLEDGE_CODE: Final[FullKnowledgeCode] = (-99, -99, -99)


class Knowledges(AttributesBase):

    __slots__ = (
        "custom_knowledge_code_name_aliases_dict",
        "custom_focus_code_name_aliases_dict",
    )
    
    def __init__(self) -> None:
        object.__setattr__(self, "custom_knowledge_code_name_aliases_dict", dict[int, StringAliases]())
        object.__setattr__(self, "custom_focus_code_name_aliases_dict", dict[int, StringAliases]())
        
        super().__init__()
    
    @property
    def focus_name_to_code(self) -> Mapping[CanonicalAlias, int]:
        """Mapping of normalized focus alias to focus code."""
        out: dict[CanonicalAlias, int] = {}
        for code, aliases in self.custom_focus_code_name_aliases_dict.items():
            for alias in aliases:
                norm_alias = _normalize(alias)
                out[norm_alias] = int(code)
        return MappingProxyType(out)

    @staticmethod
    def _generate_full_code(base_code: int) -> list[FullKnowledgeCode]:
        """Generate a full knowledge code tuple from a base knowledge code."""
        BaseKnowledgeInt = int(base_code)
        DefaultFocusInt = -99
        codes = []
        AssociatedSkillCodes = KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS.get(BaseKnowledgeInt)
        if AssociatedSkillCodes is None:
            codes.append((BaseKnowledgeInt, -99, DefaultFocusInt))
            return codes
        for AssociatedSkillInt in AssociatedSkillCodes:
            FocusInt = DefaultFocusInt
            codes.append((BaseKnowledgeInt, AssociatedSkillInt, FocusInt))

        return codes
    
    def _initialise_defaults(self) -> None:
        """Populate the default knowledges from `init_mappings.KNOWLEDGES_BASE_KNOWLEDGE_CODES`.
        
        This runs once per process. It intentionally builds a dict and then exposes it read-only.
        """
        default_map: dict[CanonicalAlias, FullKnowledgeCode] = cast(
            dict[CanonicalAlias, FullKnowledgeCode],
            self.default_canonical_alias_strkey_to_code,
        )

        for BaseKnowledgeInt, name_aliases in KNOWLEDGES_BASE_KNOWLEDGE_CODES.items():
            full_knowledge_codes = self._generate_full_code(BaseKnowledgeInt)
            for full_knowledge_code in full_knowledge_codes:
                for alias in name_aliases:
                    norm_name = _normalize(alias)
                    default_map[norm_name] = full_knowledge_code

    def _return_string_code_names(self, codes: FullKnowledgeCode) -> CodeNames:
        """Return the string code names for a given full knowledge code."""
        base_knowledge_code, associated_skill_code, focus_code = codes
        code_names: list[str] = []
        base_knowledge_aliases = KNOWLEDGES_BASE_KNOWLEDGE_CODES.get(base_knowledge_code)
        if base_knowledge_aliases:
            code_names.append(base_knowledge_aliases[0])
        else:
            code_names.append(f"UnknownKnowledgeCode{base_knowledge_code}")

        if associated_skill_code != -99:
            code_names.append(f"AssocSkill{associated_skill_code}")
        if focus_code != -99:
            code_names.append(f"Focus{focus_code}")

        return tuple(code_names)

    def return_all_aliases(self, code: int) -> StringAliases:
        """Return all aliases for a given base knowledge code."""
        aliases: list[str] = []
        base_knowledge_aliases = KNOWLEDGES_BASE_KNOWLEDGE_CODES.get(code)
        if base_knowledge_aliases:
            aliases.extend(base_knowledge_aliases)
        custom_aliases = self.custom_knowledge_code_name_aliases_dict.get(code)
        if custom_aliases:
            aliases.extend(custom_aliases)
        return tuple(aliases)

    def resolve_knowledge(self, name: str) -> tuple[FullKnowledgeCode, StringAliases]:
        """Resolve a knowledge name to its full knowledge code.

        Returns:
            FullKnowledgeCode: The resolved full knowledge code, or _UNDEFINED_FULL_KNOWLEDGE_CODE if not found.
        """
        norm_name = _normalize(name)
        combined = self.combined_view.get(norm_name, _UNDEFINED_FULL_KNOWLEDGE_CODE)
        if combined is not None:
            aliases = self.default_canonical_alias_strkey_to_code.get(norm_name)
            if aliases is None:
                aliases = self.custom_canonical_alias_strkey_to_code.get(norm_name, ("<unknown>",))
            return combined, aliases
        return _UNDEFINED_FULL_KNOWLEDGE_CODE, ("<unknown>",)
    
    def is_defined(self, name: str) -> bool:
        """Check if a knowledge name is defined."""
        norm_name = _normalize(name)
        return norm_name in self.combined_view