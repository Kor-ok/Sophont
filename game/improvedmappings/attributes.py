from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar, TypeVar

from game.improvedmappings.utils import AttributeViewHeader, DirtyDict

StringAliases = tuple[str, ...]
# Skill code is (master_category, sub_category, base_skill)
# Knowledge code is (base_knowledge_code, associated_skill_code, focus_code)
# Characteristic code is (position_code, subtype_code, master_code)
FullCode = tuple[int, int, int]

CanonicalAlias = str

TAttributesBase = TypeVar("TAttributesBase", bound="AttributesBase")


class AttributesBase:
    """Base Class for Skill, Knowledge, Characteristics Data.

    Stores default and custom alias->code mappings, and exposes a combined view.
    The combined view is rebuilt only when custom mappings are mutated (dirty-flagged).

    Full Code tuple[int, int, int]:
    - Skill code is (master_category, sub_category, base_skill)
    - Knowledge code is (base_knowledge_code, associated_skill_code, focus_code)
    - Characteristic code is (position_code, subtype_code, master_code)
    
    :param default_canonical_alias_strkey_to_code: Mutable mapping of default normalized alias -> full code.
    :param default_view_header: Header tracking max components of the default codes.
    :param default_view: Read-only mapping of default normalized alias -> full code.
    :param custom_canonical_alias_strkey_to_code: Mutable mapping of custom normalized alias -> full code.
    :param custom_view_header: Header tracking max components of the custom codes.
    :param custom_view: Read-only mapping of custom normalized alias -> full code.
    :param custom_is_dirty: Flag indicating if custom mappings have changed.
    :param combined_view: Read-only mapping of combined normalized alias -> full code.
    """

    __slots__ = (
        "default_canonical_alias_strkey_to_code",
        "default_view_header",
        "default_view",

        "custom_canonical_alias_strkey_to_code",
        "custom_view_header",
        "custom_view",
        "custom_is_dirty",

        "combined_view",
        "_is_initialised",
    )

    _instances: ClassVar[dict[type[AttributesBase], AttributesBase]] = {}

    def __new__(
        cls: type[TAttributesBase],
        *args: object,
        **kwargs: object,
    ) -> TAttributesBase:
        existing = AttributesBase._instances.get(cls)
        if existing is not None:
            return existing  # type: ignore[return-value]

        self = object.__new__(cls)

        object.__setattr__(self, "default_canonical_alias_strkey_to_code", dict[CanonicalAlias, FullCode]())
        object.__setattr__(self, "default_view_header", AttributeViewHeader())
        object.__setattr__(self, "default_view", MappingProxyType(self.default_canonical_alias_strkey_to_code))

        object.__setattr__(self, "custom_is_dirty", False)

        def _mark_dirty() -> None:
            object.__setattr__(self, "custom_is_dirty", True)

        object.__setattr__(self, "custom_canonical_alias_strkey_to_code", DirtyDict(mark_dirty=_mark_dirty))
        object.__setattr__(self, "custom_view_header", AttributeViewHeader())
        object.__setattr__(self, "custom_view", MappingProxyType(self.custom_canonical_alias_strkey_to_code))

        object.__setattr__(
            self, "combined_view", MappingProxyType(dict(self.default_canonical_alias_strkey_to_code))
        )

        object.__setattr__(self, "_is_initialised", False)
        AttributesBase._instances[cls] = self
        return self  # type: ignore[return-value]

    def __init__(self) -> None:
        if self._is_initialised:
            return
        self._initialise_defaults()
        self._refresh_views(force=True)
        object.__setattr__(self, "_is_initialised", True)

    @property
    def default_name_to_codes(self) -> Mapping[CanonicalAlias, FullCode]:
        """Read-only mapping of default normalized alias -> full code."""
        return self.default_view
    
    @property
    def custom_name_to_codes(self) -> Mapping[CanonicalAlias, FullCode]:
        """Read-only mapping of custom normalized alias -> full code."""
        return self.custom_view

    @property
    def combined_name_to_codes(self) -> Mapping[CanonicalAlias, FullCode]:
        """Read-only mapping of the combined normalized alias -> full code."""
        self._refresh_views()
        return self.combined_view

    def _refresh_views(self, *, force: bool = False) -> None:
        """Refresh derived views if custom mappings changed."""
        if not force and not self.custom_is_dirty:
            return

        self._refresh_custom_view_header()
        combined = {**self.default_canonical_alias_strkey_to_code, **self.custom_canonical_alias_strkey_to_code}
        object.__setattr__(self, "combined_view", MappingProxyType(combined))
        object.__setattr__(self, "custom_is_dirty", False)

    def _refresh_custom_view_header(self) -> None:
        """Default header refresh: tracks max components of the custom codes.

        Subclasses can override if the header has a different meaning.
        # Skill code is (master_category, sub_category, base_skill)
        # Knowledge code is (base_knowledge_code, associated_skill_code, focus_code)
        # Characteristic code is (position_code, subtype_code, master_code)
        """
        if not self.custom_canonical_alias_strkey_to_code:
            self.custom_view_header.primary_code = 0
            self.custom_view_header.secondary_code = 0
            self.custom_view_header.tertiary_code = 0
            return

        values = self.custom_canonical_alias_strkey_to_code.values()
        self.custom_view_header.primary_code = max(int(v[0]) for v in values)
        self.custom_view_header.secondary_code = max(int(v[1]) for v in values)
        self.custom_view_header.tertiary_code = max(int(v[2]) for v in values)

    @staticmethod
    def _generate_full_code(base_code: int) -> FullCode:
        """Generate a full code tuple from a base code."""
        raise NotImplementedError("Subclasses must implement _generate_full_code method.")

    def _initialise_defaults(self) -> None:
        """Initialise the default alias to code mapping. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _initialise_defaults method.")
    
    def __repr__(self) -> str:
        
        return (
            f"{self.__class__.__name__}("
            f"default_entries={len(self.default_canonical_alias_strkey_to_code)}, "
            f"custom_entries={len(self.custom_canonical_alias_strkey_to_code)})"
        )

