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
NormalizedAlias = str

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
        "_default_alias_to_code",
        "_default_view",
        "_custom_alias_to_code",
        "_custom_view",
        "_custom_base_skill_code_to_aliases",
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
        object.__setattr__(self, "_default_alias_to_code", dict[NormalizedAlias, FullSkillCode]())
        object.__setattr__(self, "_default_view", MappingProxyType(self._default_alias_to_code))
        object.__setattr__(self, "_custom_alias_to_code", dict[NormalizedAlias, FullSkillCode]())
        object.__setattr__(self, "_custom_view", MappingProxyType(self._custom_alias_to_code))
        object.__setattr__(self, "_custom_base_skill_code_to_aliases", dict[int, StringAliases]())
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
    def default_skill_name_to_codes(self) -> Mapping[NormalizedAlias, FullSkillCode]:
        """Read-only mapping of default normalized alias -> full skill code."""
        return self._default_view

    @property
    def custom_skill_name_to_codes(self) -> Mapping[NormalizedAlias, FullSkillCode]:
        """Read-only mapping of custom normalized alias -> full skill code."""
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
        default_map: dict[NormalizedAlias, FullSkillCode] = self._default_alias_to_code
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
        """Given a full skill code, return canonical string aliases.

        Returns (master_category, sub_category, base_skill) aliases where possible.
        """
        master_cat, sub_cat, base_code = codes
        aliases: list[str] = []
        master_aliases = _MASTER_CATEGORY_CODES.get(master_cat)
        if master_aliases:
            aliases.append(master_aliases[0])
        else:
            custom_master_aliases = self.custom_master_category_dict.get(master_cat)
            if custom_master_aliases:
                aliases.append(custom_master_aliases[0])
        sub_aliases = _SUB_CATEGORY_CODES.get(sub_cat)
        if sub_aliases:
            aliases.append(sub_aliases[0])
        else:
            custom_sub_aliases = self.custom_sub_category_dict.get(sub_cat)
            if custom_sub_aliases:
                aliases.append(custom_sub_aliases[0])
        base_aliases = _BASE_SKILL_CODES.get(base_code)
        if base_aliases:
            aliases.append(base_aliases[0])
        else:
            custom_base_aliases = self._custom_base_skill_code_to_aliases.get(base_code)
            if custom_base_aliases:
                aliases.append(custom_base_aliases[0])

        return tuple(aliases)

    def resolve(self, name: str) -> tuple[FullSkillCode, StringAliases]:
        """Resolve a skill name/alias to its full skill code and string aliases.

        Custom skills take precedence *if* a custom alias exists.
        """
        norm = _normalize(name)
        custom = self._custom_alias_to_code.get(norm)
        if custom is not None:
            aliases = self._return_string_names(custom)
            return custom, aliases
        default = self._default_alias_to_code.get(norm, _UNDEFINED_FULL_SKILL_CODE)
        aliases = self._return_string_names(default)
        return default, aliases

    def is_defined(self, name: str) -> bool:
        code, _aliases = self.resolve(name)
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

        normalized_skill_aliases: tuple[NormalizedAlias, ...] = tuple(
            _normalize(a) for a in skill_aliases
        )

        # Validate collisions with defaults.
        if not allow_override_default:
            for norm in normalized_skill_aliases:
                if norm in self._default_alias_to_code:
                    return f"Cannot override default skill alias: {skill_aliases!r}"

        # Validate collisions with existing customs.
        if not replace:
            for norm in normalized_skill_aliases:
                if norm in self._custom_alias_to_code:
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
                max(self._custom_base_skill_code_to_aliases.keys(), default=0),
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
                self._custom_alias_to_code.pop(norm, None)

        for norm in normalized_skill_aliases:
            self._custom_alias_to_code[norm] = new_full_code

        # Store canonical (display) aliases for the new base skill.
        self._custom_base_skill_code_to_aliases[next_base_code] = skill_aliases

        self.custom_skills_dict_attributes.highest_base_code = max(
            (code[2] for code in self._custom_alias_to_code.values()),
            default=0,
        )

        return (
            f"Using base skill code {next_base_code} for {skill_aliases!r}"
            f"\nUsing master category code {master_cat_code} for {master_aliases!r}"
            f"\nUsing sub category code {sub_cat_code} for {sub_aliases!r}"
        )

    def unregister_custom(self, name_or_alias: str) -> bool:
        """Remove a custom alias. Returns True if removed."""
        norm = _normalize(name_or_alias)
        removed = self._custom_alias_to_code.pop(norm, None) is not None
        if removed:
            used_base_codes = {code[2] for code in self._custom_alias_to_code.values()}
            for base_code in list(self._custom_base_skill_code_to_aliases.keys()):
                if base_code not in used_base_codes:
                    self._custom_base_skill_code_to_aliases.pop(base_code, None)
            self.custom_skills_dict_attributes.highest_base_code = max(used_base_codes, default=0)
        return removed

    def clear_custom(self) -> None:
        self._custom_alias_to_code.clear()
        self._custom_base_skill_code_to_aliases.clear()
        self.custom_master_category_dict.clear()
        self.custom_sub_category_dict.clear()
        self.custom_skills_dict_attributes.highest_base_code = 0


# Convenience singleton instance for app-wide usage.
SKILLS: Final[SkillSet] = SkillSet()
