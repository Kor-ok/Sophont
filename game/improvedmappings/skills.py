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

StringAliases = tuple[str, ...]
FullSkillCode = tuple[int, int, int]  # (master_category, sub_category, base_skill)

_UNDEFINED_FULL_SKILL_CODE: Final[FullSkillCode] = (-99, -99, -99)


@lru_cache(maxsize=4096)
def _normalize(name: str) -> str:
    # case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    return " ".join(name.strip().casefold().split())


class SkillDictAttributes:
    __slots__ = ("base_codes_size", "master_category_codes_size", "sub_category_codes_size")

    def __init__(
        self,
        base_codes_size: int,
        master_category_codes_size: int,
        sub_category_codes_size: int,
    ) -> None:
        self.base_codes_size = int(base_codes_size)
        self.master_category_codes_size = int(master_category_codes_size)
        self.sub_category_codes_size = int(sub_category_codes_size)


class SkillSet:
    """App-wide store for RPG skills.

    - Default skills are loaded from `game.improvedmappings.skill_tables` once and then exposed read-only.
    - Custom skills can be registered/removed at runtime.
    - Lookups are normalized (`casefold` + collapsed whitespace).

    This is implemented as a singleton so all callers share the same store:

        skills = SkillSet()  # always returns the same instance
    """

    __slots__ = (
        "_default_name_to_code",
        "_default_view",
        "_custom_name_to_code",
        "_custom_view",
        "default_skills_dict_attributes",
        "custom_skills_dict_attributes",
        "_is_initialized",
    )

    _instance: Optional[SkillSet] = None

    def __new__(cls) -> SkillSet:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "_default_name_to_code", {})
        object.__setattr__(self, "_default_view", MappingProxyType(self._default_name_to_code))
        object.__setattr__(self, "_custom_name_to_code", {})
        object.__setattr__(self, "_custom_view", MappingProxyType(self._custom_name_to_code))
        object.__setattr__(
            self,
            "default_skills_dict_attributes",
            SkillDictAttributes(
                len(_BASE_SKILL_CODES), len(_MASTER_CATEGORY_CODES), len(_SUB_CATEGORY_CODES)
            ),
        )
        object.__setattr__(
            self,
            "custom_skills_dict_attributes",
            SkillDictAttributes(0, 0, 0),
        )
        object.__setattr__(self, "_is_initialized", False)
        cls._instance = self
        return self

    def __init__(self) -> None:
        if self._is_initialized:
            return
        self._initialise_defaults()
        object.__setattr__(self, "_is_initialized", True)

    @property
    def default_skill_name_to_codes(self) -> Mapping[str, FullSkillCode]:
        """Read-only mapping of default normalized name -> full skill code."""
        return self._default_view

    @property
    def custom_skill_name_to_codes(self) -> Mapping[str, FullSkillCode]:
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
        default_map: dict[str, FullSkillCode] = self._default_name_to_code
        for base_code, name_aliases in _BASE_SKILL_CODES.items():
            full_skill_code = self._generate_full_skill_code(base_code)
            for alias in name_aliases:
                norm_name = _normalize(alias)
                existing = default_map.get(norm_name)
                if existing is not None and existing != full_skill_code:
                    raise ValueError(
                        f"Default alias collision for {alias!r} ({norm_name!r}): {existing} vs {full_skill_code}"
                    )
                default_map[norm_name] = full_skill_code

    def _return_string_names(self, codes: FullSkillCode) -> StringAliases:
        """Given a full skill code, return all default string aliases for it."""
        master_cat, sub_cat, base_code = codes
        aliases: StringAliases = ()
        aliases += _MASTER_CATEGORY_CODES.get(master_cat, ())
        aliases += _SUB_CATEGORY_CODES.get(sub_cat, ())
        aliases += _BASE_SKILL_CODES.get(base_code, ())
        return tuple(aliases)

    def resolve(self, name: str) -> tuple[FullSkillCode, StringAliases]:
        """Resolve a skill name/alias to its full skill code and string aliases.

        Custom skills take precedence *if* a custom alias exists.
        """
        norm = _normalize(name)
        custom = self._custom_name_to_code.get(norm)
        if custom is not None:
            aliases = self._return_string_names(custom)
            return custom, aliases
        default = self._default_name_to_code.get(norm, _UNDEFINED_FULL_SKILL_CODE)
        aliases = self._return_string_names(default)
        return default, aliases

    def is_defined(self, name: str) -> bool:
        return self.resolve(name) != _UNDEFINED_FULL_SKILL_CODE

    def register_custom(
        self,
        *,
        name: str,
        full_code: FullSkillCode,
        aliases: Iterable[str] = (),
        allow_override_default: bool = False,
        replace: bool = False,
    ) -> None:
        """Register a custom skill name (+ optional aliases) to a full skill code.

        Rules:
        - The default mapping is never mutated.
        - By default, you cannot shadow a default alias.
        - By default, you cannot overwrite an existing custom alias.
        """

        normalized_keys = [_normalize(name), *(_normalize(a) for a in aliases)]
        if not allow_override_default:
            for k in normalized_keys:
                if k in self._default_name_to_code:
                    raise ValueError(f"Cannot override default skill alias: {k!r}")

        for k in normalized_keys:
            if not replace and k in self._custom_name_to_code:
                raise ValueError(f"Custom skill alias already registered: {k!r}")

        for k in normalized_keys:
            self._custom_name_to_code[k] = (
                int(full_code[0]),
                int(full_code[1]),
                int(full_code[2]),
            )

        self.custom_skills_dict_attributes.base_codes_size = len(self._custom_name_to_code)

    def register_custom_by_base_code(
        self,
        *,
        name: str,
        base_code: int,
        aliases: Iterable[str] = (),
        allow_override_default: bool = False,
        replace: bool = False,
    ) -> None:
        """Register a custom skill using the default category mapping for the given base code."""
        self.register_custom(
            name=name,
            full_code=self._generate_full_skill_code(base_code),
            aliases=aliases,
            allow_override_default=allow_override_default,
            replace=replace,
        )

    def unregister_custom(self, name_or_alias: str) -> bool:
        """Remove a custom alias. Returns True if removed."""
        norm = _normalize(name_or_alias)
        removed = self._custom_name_to_code.pop(norm, None) is not None
        if removed:
            self.custom_skills_dict_attributes.base_codes_size = len(self._custom_name_to_code)
        return removed

    def clear_custom(self) -> None:
        self._custom_name_to_code.clear()
        self.custom_skills_dict_attributes.base_codes_size = 0


# Convenience singleton instance for app-wide usage.
SKILLS: Final[SkillSet] = SkillSet()
