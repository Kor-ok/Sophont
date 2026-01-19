from __future__ import annotations

from collections.abc import Iterable
from typing import Final, cast

from game.improvedmappings.attributes import AttributesBase
from game.improvedmappings.skill_tables import (
    _BASE_SKILL_CODES,
    _MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
    _MASTER_CATEGORY_CODES,
    _SUB_CATEGORY_CODES,
)
from game.improvedmappings.utils import AttributeViewHeader, _normalize

StringAliases = tuple[str, ...]

MasterCategoryInt = int
SubCategoryInt = int
BaseSkillInt = int
FullSkillCode = tuple[MasterCategoryInt, SubCategoryInt, BaseSkillInt]

CanonicalAlias = str

_UNDEFINED_FULL_SKILL_CODE: Final[FullSkillCode] = (-99, -99, -99)

class Skills(AttributesBase):
    """Handles populating default skills and managing the mapping of custom skills.
    
    """
    __slots__ = (
        "custom_skill_code_dict",
        "custom_master_category_dict",
        "custom_sub_category_dict",
    )

    def __init__(self) -> None:
        try:
            self.custom_skill_code_dict
        except AttributeError:
            object.__setattr__(self, "custom_skill_code_dict", dict[int, StringAliases]())
            object.__setattr__(self, "custom_master_category_dict", dict[int, StringAliases]())
            object.__setattr__(self, "custom_sub_category_dict", dict[int, StringAliases]())

        super().__init__()

    @staticmethod
    def _generate_full_code(base_code: int) -> FullSkillCode:
        """Given a base skill code, return (master_category, sub_category, base_skill)."""
        BaseSkillInt = int(base_code)
        categories = _MAPPING_BASE_SKILL_CODE_TO_CATEGORIES.get(BaseSkillInt)
        if categories is None:
            return (-99, -99, BaseSkillInt)
        MasterCategoryInt, SubCategoryInt = categories
        return (int(MasterCategoryInt), int(SubCategoryInt), BaseSkillInt)

    def _initialise_defaults(self) -> None:
        """Populate the default mapping from the skill tables.

        This runs once per process. It intentionally builds a dict and then exposes it read-only.
        """
        self.default_view_header: AttributeViewHeader # to advertise the skill code-space.
        self.default_view_header.primary_code = max(_MASTER_CATEGORY_CODES)
        self.default_view_header.secondary_code = max(_SUB_CATEGORY_CODES)
        self.default_view_header.tertiary_code = max(_BASE_SKILL_CODES)

        default_map: dict[CanonicalAlias, FullSkillCode] = cast(
            dict[CanonicalAlias, FullSkillCode],
            self.default_canonical_alias_key_to_code,
        )
        for BaseSkillInt, name_aliases in _BASE_SKILL_CODES.items():
            full_skill_code = self._generate_full_code(BaseSkillInt)
            for alias in name_aliases:
                norm_name = _normalize(alias)
                existing = default_map.get(norm_name)
                if existing is not None and existing != full_skill_code:
                    raise ValueError(
                        f"Default alias collision for {alias!r} ({norm_name!r}): {existing} vs {full_skill_code}"
                    )
                default_map[norm_name] = full_skill_code

    def _return_skill_string_names(self, codes: FullSkillCode) -> StringAliases:
        """Given a full skill code, return canonical string aliases.

        Returns (master_category, sub_category, base_skill) aliases where possible.
        """
        MasterCategoryInt, SubCategoryInt, BaseSkillInt = codes
        aliases: list[str] = []
        master_aliases = _MASTER_CATEGORY_CODES.get(MasterCategoryInt)
        if master_aliases:
            aliases.append(master_aliases[0])
        else:
            custom_master_aliases = self.custom_master_category_dict.get(MasterCategoryInt)
            if custom_master_aliases:
                aliases.append(custom_master_aliases[0])
        sub_aliases = _SUB_CATEGORY_CODES.get(SubCategoryInt)
        if sub_aliases:
            aliases.append(sub_aliases[0])
        else:
            custom_sub_aliases = self.custom_sub_category_dict.get(SubCategoryInt)
            if custom_sub_aliases:
                aliases.append(custom_sub_aliases[0])
        base_aliases = _BASE_SKILL_CODES.get(BaseSkillInt)
        if base_aliases:
            aliases.append(base_aliases[0])
        else:
            custom_base_aliases = self.custom_skill_code_dict.get(
                BaseSkillInt
            )
            if custom_base_aliases:
                aliases.append(custom_base_aliases[0])

        return tuple(aliases)

    def resolve_skill(self, name: str) -> tuple[FullSkillCode, StringAliases]:
        """Resolve a skill name/alias to its full skill code and string aliases.

        Custom skills take precedence *if* a custom alias exists.
        """
        norm = _normalize(name)
        custom = self.custom_canonical_alias_key_to_code.get(norm)
        if custom is not None:
            aliases = self._return_skill_string_names(custom)
            return custom, aliases
        default = self.default_canonical_alias_key_to_code.get(
            norm, _UNDEFINED_FULL_SKILL_CODE
        )
        aliases = self._return_skill_string_names(default)
        return default, aliases

    def is_defined(self, name: str) -> bool:
        code, _aliases = self.resolve_skill(name)
        return code != _UNDEFINED_FULL_SKILL_CODE
    
    def register_custom_skill(
        self,
        *,
        skill_name: Iterable[str],
        master_category_name: Iterable[str],
        sub_category_name: Iterable[str],
        allow_override_default: bool = False,
        replace: bool = False,
    ) -> str:
        """Register a custom skill using string names instead of `FullSkillCode`.

        Uses the first element of each iterable as the canonical display name.

        This should automatically manage the custom base skill code so that it does not conflict
        with existing default or custom base skill codes.
        """
        skill_aliases: StringAliases = tuple(skill_name)
        master_aliases: StringAliases = tuple(master_category_name)
        sub_aliases: StringAliases = tuple(sub_category_name)
        if not skill_aliases or not master_aliases or not sub_aliases:
            raise ValueError("skill_name/master_category_name/sub_category_name must be non-empty")

        normalized_skill_aliases: tuple[CanonicalAlias, ...] = tuple(
            _normalize(a) for a in skill_aliases
        )

        # Validate collisions with defaults.
        if not allow_override_default:
            for norm in normalized_skill_aliases:
                if norm in self.default_canonical_alias_key_to_code:
                    return f"Cannot override default skill alias: {skill_aliases!r}"

        # Validate collisions with existing customs.
        if not replace:
            for norm in normalized_skill_aliases:
                if norm in self.custom_canonical_alias_key_to_code:
                    return f"Custom skill alias already exists: {skill_aliases!r}"

        # Determine / allocate master category code.
        norm_master = tuple(_normalize(a) for a in master_aliases)
        master_cat_code: int | None = None
        for code, aliases in _MASTER_CATEGORY_CODES.items():
            if any(_normalize(a) in norm_master for a in aliases):
                master_cat_code = int(code)
                break
        if master_cat_code is None:
            for code, aliases in self.custom_master_category_dict.items():
                if any(_normalize(a) in norm_master for a in aliases):
                    master_cat_code = int(code)
                    break
        if master_cat_code is None:
            master_cat_code = (
                max(
                    max(_MASTER_CATEGORY_CODES.keys(), default=0),
                    max(self.custom_master_category_dict.keys(), default=0),
                )
                + 1
            )
            self.custom_master_category_dict[master_cat_code] = master_aliases
        # Determine / allocate sub category code.
        norm_sub = tuple(_normalize(a) for a in sub_aliases)
        sub_cat_code: int | None = None
        for code, aliases in _SUB_CATEGORY_CODES.items():
            if any(_normalize(a) in norm_sub for a in aliases):
                sub_cat_code = int(code)
                break
        if sub_cat_code is None:
            for code, aliases in self.custom_sub_category_dict.items():
                if any(_normalize(a) in norm_sub for a in aliases):
                    sub_cat_code = int(code)
                    break
        if sub_cat_code is None:
            sub_cat_code = (
                max(
                    max(_SUB_CATEGORY_CODES.keys(), default=0),
                    max(self.custom_sub_category_dict.keys(), default=0),
                )
                + 1
            )
            self.custom_sub_category_dict[sub_cat_code] = sub_aliases
        # Allocate a base skill code that does not collide.
        next_base_code = (
            max(
                max(_BASE_SKILL_CODES.keys(), default=0),
                max(self.custom_skill_code_dict.keys(), default=0),
            )
            + 1
        )
        new_full_code: FullSkillCode = (
            int(master_cat_code),
            int(sub_cat_code),
            int(next_base_code),
        )

        # If replacing, remove any of these aliases first.
        if replace:
            for norm in normalized_skill_aliases:
                self.custom_canonical_alias_key_to_code.pop(norm, None)

        for norm in normalized_skill_aliases:
            self.custom_canonical_alias_key_to_code[norm] = new_full_code

        # Store canonical (display) aliases for the new base skill.
        self.custom_skill_code_dict[next_base_code] = skill_aliases

        self.custom_view_header.highest_base_code = max(
            (code[2] for code in self.custom_canonical_alias_key_to_code.values()),
            default=0,
        )

        return (
            f"Using base skill code {next_base_code} for {skill_aliases!r}"
            f"\nUsing master category code {master_cat_code} for {master_aliases!r}"
            f"\nUsing sub category code {sub_cat_code} for {sub_aliases!r}"
        )

    def unregister_custom_skill(self, name_or_alias: str) -> bool:
        """Remove a custom alias. Returns True if removed."""
        norm = _normalize(name_or_alias)
        removed = self.custom_canonical_alias_key_to_code.pop(norm, None) is not None
        if removed:
            used_base_codes = {code[2] for code in self.custom_canonical_alias_key_to_code.values()}
            for base_code in list(self.custom_skill_code_dict.keys()):
                if base_code not in used_base_codes:
                    self.custom_skill_code_dict.pop(base_code, None)
            self.custom_view_header.highest_base_code = max(used_base_codes, default=0)
        return removed

    def clear_custom_skills(self) -> None:
        self.custom_canonical_alias_key_to_code.clear()
        self.custom_skill_code_dict.clear()
        self.custom_master_category_dict.clear()
        self.custom_sub_category_dict.clear()
        self.custom_view_header.highest_base_code = 0