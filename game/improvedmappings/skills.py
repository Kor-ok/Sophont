from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import lru_cache
from types import MappingProxyType
from typing import Final, Optional

from game.improvedmappings.skill_tables import (
    _BASE_SKILL_CODES,
    _MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
    _MASTER_CATEGORY_CODES,
    _SUB_CATEGORY_CODES,
)

# TODO: Streamline all of this.

StringAliases = tuple[str, ...]
FullSkillCode = tuple[int, int, int]  # (master_category, sub_category, base_skill)

_UNDEFINED_FULL_SKILL_CODE: Final[FullSkillCode] = (-99, -99, -99)


@lru_cache(maxsize=4096)
def _normalize(name: str | Iterable[str]) -> str:
    # case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    # Also works with tuples of strings.
    if isinstance(name, Iterable) and not isinstance(name, str):
        name = " ".join(name)

    return " ".join(name.strip().casefold().split())


class SkillDictAttributes:
    __slots__ = ("highest_base_code", "highest_master_category_code", "highest_sub_category_code")

    def __init__(
        self,
        highest_base_code: int,
        highest_master_category_code: int,
        highest_sub_category_code: int,
    ) -> None:
        self.highest_base_code = int(highest_base_code)
        self.highest_master_category_code = int(highest_master_category_code)
        self.highest_sub_category_code = int(highest_sub_category_code)


class SkillSet:
    """App-wide store for RPG skills.

    - Default skills are loaded from `game.improvedmappings.skill_tables` once and then exposed read-only.
    - Custom skills can be registered/removed at runtime.
    - Custom master and sub category code tables can be extended/culled at runtime.
    - Lookups are normalized (`casefold` + collapsed whitespace).

    This is implemented as a singleton so all callers share the same store:

        skills = SkillSet()  # always returns the same instance
    """

    __slots__ = (
        "_default_names_to_code",
        "_default_view",
        "_custom_names_to_code",
        "_custom_view",
        "default_skills_dict_attributes",
        "custom_skills_dict_attributes",
        "custom_master_category_dict",
        "custom_sub_category_dict",
        "_is_initialized",
    )

    _instance: Optional[SkillSet] = None

    def __new__(cls) -> SkillSet:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "_default_names_to_code", dict[StringAliases, FullSkillCode]())
        object.__setattr__(self, "_default_view", MappingProxyType(self._default_names_to_code))
        object.__setattr__(self, "_custom_names_to_code", dict[StringAliases, FullSkillCode]())
        object.__setattr__(self, "_custom_view", MappingProxyType(self._custom_names_to_code))
        object.__setattr__(
            self,
            "default_skills_dict_attributes",
            SkillDictAttributes(
                max(_BASE_SKILL_CODES), max(_MASTER_CATEGORY_CODES), max(_SUB_CATEGORY_CODES)
            ),
        )
        object.__setattr__(
            self,
            "custom_skills_dict_attributes",
            SkillDictAttributes(0, 0, 0),
        )
        object.__setattr__(self, "custom_master_category_dict", dict[int, StringAliases]())
        object.__setattr__(self, "custom_sub_category_dict", dict[int, StringAliases]())
        object.__setattr__(self, "_is_initialized", False)
        cls._instance = self
        return self

    def __init__(self) -> None:
        if self._is_initialized:
            return
        self._initialise_defaults()
        object.__setattr__(self, "_is_initialized", True)

    @property
    def default_skill_name_to_codes(self) -> Mapping[StringAliases, FullSkillCode]:
        """Read-only mapping of default normalized name -> full skill code."""
        return self._default_view

    @property
    def custom_skill_name_to_codes(self) -> Mapping[StringAliases, FullSkillCode]:
        """Read-only mapping of custom normalized name -> full skill code."""
        return self._custom_view

    def _generate_full_skill_code(self, base_code: int) -> FullSkillCode:
        """Given a base skill code, return (master_category, sub_category, base_skill)."""
        base_code_int = int(base_code)
        categories = _MAPPING_BASE_SKILL_CODE_TO_CATEGORIES.get(base_code_int)
        if categories is None:
            return (-99, -99, base_code_int)
        master_cat, sub_cat = categories
        return (int(master_cat), int(sub_cat), base_code_int)

    def _initialise_defaults(self) -> None:
        """Populate the default mapping from the skill tables.

        This runs once per process. It intentionally builds a dict and then exposes it read-only.
        """
        default_map: dict[StringAliases, FullSkillCode] = self._default_names_to_code
        for base_code, name_aliases in _BASE_SKILL_CODES.items():
            full_skill_code = self._generate_full_skill_code(base_code)
            for alias in name_aliases:
                norm_name = _normalize(alias)
                existing = default_map.get(norm_name)
                if existing is not None and existing != full_skill_code:
                    raise ValueError(
                        f"Default alias collision for {alias!r} ({norm_name!r}): {existing} vs {full_skill_code}"
                    )
                default_map[(norm_name,)] = full_skill_code

    def _return_string_names(self, codes: FullSkillCode) -> StringAliases:
        """Given a full skill code, return the first default string alias for each tuple value"""
        master_cat, sub_cat, base_code = codes
        aliases: StringAliases = ()
        master_aliases = _MASTER_CATEGORY_CODES.get(master_cat)
        if master_aliases:
            aliases += (master_aliases[0],)
        else:
            # search custom master category codes
            master_aliases = self.custom_master_category_dict.get(master_cat)
            if master_aliases:
                aliases += (master_aliases,)
        sub_aliases = _SUB_CATEGORY_CODES.get(sub_cat)
        if sub_aliases:
            aliases += (sub_aliases[0],)
        else:
            # search custom sub category codes
            sub_aliases = self.custom_sub_category_dict.get(sub_cat)
            if sub_aliases:
                aliases += (sub_aliases,)
        base_aliases = _BASE_SKILL_CODES.get(base_code)
        if base_aliases:
            aliases += (base_aliases[0],)
        else:
            # search custom base skill codes
            for str_aliases, codes_tuple in self._custom_names_to_code.items():
                if codes_tuple == codes:
                    aliases += (str_aliases,)
                    break
        return tuple(aliases)

    def resolve(self, name: str) -> tuple[FullSkillCode, StringAliases]:
        """Resolve a skill name/alias to its full skill code and string aliases.

        Custom skills take precedence *if* a custom alias exists.
        """
        norm = _normalize(name)
        custom = self._custom_names_to_code.get(norm)
        if custom is not None:
            aliases = self._return_string_names(custom)
            return custom, aliases
        default = self._default_names_to_code.get(norm, _UNDEFINED_FULL_SKILL_CODE)
        aliases = self._return_string_names(default)
        return default, aliases

    def is_defined(self, name: str) -> bool:
        return self.resolve(name) != _UNDEFINED_FULL_SKILL_CODE

    def register_custom_skill(
        self,
        *,
        skill_name: Iterable[str],
        master_category_name: Iterable[str],
        sub_category_name: Iterable[str],
        allow_override_default: bool = False,
        replace: bool = False,
    ) -> str: # Feedback for the confirmation of registered details.
        """ Register a custom skill using string names instead of FullSkillCode.

        Will use the first of the iterables as the canonical name for shallow validation logic.

        This should automatically manage the custom base skill code so that it does not conflict
        with existing default or custom base skill codes through checks and incrementing.
        """
        # First check that skill_name does not already exist in default names.
        _norm_skill_name = _normalize(skill_name)
        if _norm_skill_name in self._default_names_to_code:
            return_mesage = f"Cannot override default skill alias: {skill_name}"
            return return_mesage
        
        # Next find the next available base skill code to use
        if self.custom_skills_dict_attributes.highest_base_code == 0:
            next_base_code = max(code[2] for code in self._default_names_to_code.values()) + 1
        else:
            next_base_code = max(code[2] for code in self._custom_names_to_code.values()) + 1

        # Now resolve the master and sub category names to their codes, adding to custom dicts if needed.
        _norm_master_category_name = _normalize(master_category_name)
        cat_name_found = False
        for code, aliases in _MASTER_CATEGORY_CODES.items():
            if _norm_master_category_name in [a for a in aliases]:
                master_cat_code = code
                cat_name_found = True
        for custom_code, custom_name in self.custom_master_category_dict.items():
            if _norm_master_category_name == _normalize(custom_name):
                master_cat_code = custom_code
                cat_name_found = True
        if not cat_name_found:
            # Add to custom master category dict
            next_custom_master_cat_code = max(self.custom_master_category_dict.values()) if self.custom_master_category_dict else 0
            next_default_master_cat_code = max(_MASTER_CATEGORY_CODES.keys())
            master_cat_code = max(next_custom_master_cat_code, next_default_master_cat_code) + 1
            self.custom_master_category_dict[master_cat_code] = _norm_master_category_name

        _norm_sub_category_name = _normalize(sub_category_name)
        sub_cat_name_found = False        
        for code, aliases in _SUB_CATEGORY_CODES.items():
            if _norm_sub_category_name in [a for a in aliases]:
                sub_cat_code = code
                sub_cat_name_found = True
        for custom_code, custom_name in self.custom_sub_category_dict.items():
            if _norm_sub_category_name == _normalize(custom_name):
                sub_cat_code = custom_code
                sub_cat_name_found = True
        if not sub_cat_name_found:
                # Add to custom sub category dict
                next_custom_sub_cat_code = max(self.custom_sub_category_dict.values()) if self.custom_sub_category_dict else 0
                next_default_sub_cat_code = max(_SUB_CATEGORY_CODES.keys())
                sub_cat_code = max(next_custom_sub_cat_code, next_default_sub_cat_code) + 1
                self.custom_sub_category_dict[sub_cat_code] = _normalize(sub_category_name)
        
        return_mesage = f"Using base skill code {next_base_code} for {skill_name}" + \
                        f"\nUsing master category code {master_cat_code} for {master_category_name}" + \
                        f"\nUsing sub category code {sub_cat_code} for {sub_category_name}"
        
        new_full_code = (master_cat_code, sub_cat_code, next_base_code)
        
        normalized_keys = [_norm_skill_name, *(a for a in aliases)]

        for k in normalized_keys:
            self._custom_names_to_code[k] = (
                int(new_full_code[0]),
                int(new_full_code[1]),
                int(new_full_code[2]),
            )

        self.custom_skills_dict_attributes.highest_base_code = max(code[2] for code in self._custom_names_to_code.values())

        return return_mesage

    def unregister_custom(self, name_or_alias: str) -> bool:
        """Remove a custom alias. Returns True if removed."""
        norm = _normalize(name_or_alias)
        removed = self._custom_names_to_code.pop(norm, None) is not None
        if removed:
            self.custom_skills_dict_attributes.highest_base_code = max(code[2] for code in self._custom_names_to_code.values()) if self._custom_names_to_code else 0
        return removed

    def clear_custom(self) -> None:
        self._custom_names_to_code.clear()
        self.custom_skills_dict_attributes.highest_base_code = 0


# Convenience singleton instance for app-wide usage.
SKILLS: Final[SkillSet] = SkillSet()
