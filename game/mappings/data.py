from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from enum import Enum
from types import MappingProxyType
from typing import Any, Final

from typing_extensions import TypeAlias

from game.mappings.utils import AttributeViewHeader, _normalize


class MutabilityLevel(Enum):
    DEFAULT = "default"
    CUSTOM = "custom"
    COMBINED = "combined"


CanonicalStrKey: TypeAlias = str
CanonicalCodeInt: TypeAlias = int
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]

PrimaryCodeInt: TypeAlias = int
SecondaryCodeInt: TypeAlias = int
TertiaryCodeInt: TypeAlias = int
FullCode: TypeAlias = tuple[PrimaryCodeInt, SecondaryCodeInt, TertiaryCodeInt]
"""
- Skill code is (master_category, sub_category, base_skill)
- Knowledge code is (base_knowledge_code, associated_skill_code, focus_code)
- Characteristic code is (position_code, subtype_code, master_code)
"""

AliasMappedFullCode: TypeAlias = tuple[AliasMap, FullCode]

# Shape of the Data:
# - AliasMap: { canonical_key: (alias1, alias2, ...) }
# - FullCode: (int, int, int)
# - Entry: (AliasMap, FullCode)


def _is_full_code(value: object) -> bool:
    if not isinstance(value, tuple) or len(value) != 3:
        return False
    return all(isinstance(x, int) for x in value)


class DirtyCollection(list[AliasMappedFullCode]):
    """A list-like collection that tracks if it has been modified."""

    __slots__ = ("is_dirty", "version", "_on_change")

    def __init__(
        self,
        iterable: Iterable[AliasMappedFullCode] = (),
        *,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(iterable)
        self.is_dirty: bool = False
        self.version: int = 0
        self._on_change = on_change

    def _bump(self) -> None:
        self.is_dirty = True
        self.version += 1
        if self._on_change is not None:
            self._on_change()

    def mark_clean(self) -> None:
        self.is_dirty = False

    def append(self, __object: AliasMappedFullCode) -> None:  # type: ignore[override]
        super().append(__object)
        self._bump()

    def extend(self, __iterable: Iterable[AliasMappedFullCode]) -> None:  # type: ignore[override]
        super().extend(__iterable)
        self._bump()

    def insert(self, __index: int, __object: AliasMappedFullCode) -> None:  # type: ignore[override]
        super().insert(__index, __object)
        self._bump()

    def remove(self, __value: AliasMappedFullCode) -> None:  # type: ignore[override]
        super().remove(__value)
        self._bump()

    def pop(self, __index: int = -1) -> AliasMappedFullCode:  # type: ignore[override]
        value = super().pop(__index)
        self._bump()
        return value

    def clear(self) -> None:  # type: ignore[override]
        super().clear()
        self._bump()

    def __setitem__(self, key: int | slice, value: Any) -> None:  # type: ignore[override]
        super().__setitem__(key, value)
        self._bump()

    def __delitem__(self, key: int | slice) -> None:  # type: ignore[override]
        super().__delitem__(key)
        self._bump()

    def __iadd__(self, other: Iterable[AliasMappedFullCode]) -> DirtyCollection:  # type: ignore[override]
        result = super().__iadd__(other)
        self._bump()
        return result

    def __imul__(self, n: int) -> DirtyCollection:  # type: ignore[override]
        result = super().__imul__(n)
        self._bump()
        return result


class AliasMappedFullCodeCollection:

    __slots__ = (
        "mutability",
        "collection",
        "header",
        "alias_to_code",
        "canonical_to_code",
        "code_to_names",
    )

    mutability: MutabilityLevel
    collection: DirtyCollection
    header: AttributeViewHeader

    alias_to_code: Mapping[str, FullCode]
    canonical_to_code: Mapping[str, FullCode]
    code_to_names: Mapping[FullCode, tuple[CanonicalStrKey, StringAliases]]

    _EMPTY: Final[Mapping[Any, Any]] = MappingProxyType({})

    def __init__(
        self,
        *,
        mutability: MutabilityLevel,
        collection: Iterable[AliasMappedFullCode] = (),
        header: AttributeViewHeader | None = None,
    ) -> None:
        self.mutability = mutability
        self.header = header if header is not None else AttributeViewHeader()

        self.collection = DirtyCollection(
            collection,
            on_change=self._refresh_header_from_collection,
        )

        self.alias_to_code = self._EMPTY  # type: ignore[assignment]
        self.canonical_to_code = self._EMPTY  # type: ignore[assignment]
        self.code_to_names = self._EMPTY  # type: ignore[assignment]

        # Ensure first query builds indexes.
        self.collection.is_dirty = True

        # Ensure header reflects the initial collection.
        self._refresh_header_from_collection()

    def _refresh_header_from_collection(self) -> None:
        """Update `header` to reflect the current collection.

        The collection's FullCode tuples map directly to:
        - primary_code
        - secondary_code
        - tertiary_code

        We track the highest value seen for each component.
        """
        primary = -1
        secondary = -1
        tertiary = -1

        for _, (a, b, c) in self.collection:
            if a > primary:
                primary = a
            if b > secondary:
                secondary = b
            if c > tertiary:
                tertiary = c

        self.header.primary_code = primary
        self.header.secondary_code = secondary
        self.header.tertiary_code = tertiary

    @classmethod
    def from_iterable(
        cls,
        *,
        mutability: MutabilityLevel,
        entries: Iterable[AliasMappedFullCode],
    ) -> AliasMappedFullCodeCollection:
        return cls(mutability=mutability, collection=entries)

    def _rebuild_indexes(self) -> None:
        alias_to_code: dict[str, FullCode] = {}
        canonical_to_code: dict[str, FullCode] = {}
        code_to_names: dict[FullCode, tuple[CanonicalStrKey, StringAliases]] = {}

        for alias_map, code in self.collection:
            for canonical, aliases in alias_map.items():
                canonical_norm = _normalize(canonical)

                existing_code = canonical_to_code.get(canonical_norm)
                if existing_code is not None and existing_code != code:
                    raise ValueError(
                        "Canonical collision: "
                        f"{canonical!r} maps to both {existing_code} and {code}"
                    )
                canonical_to_code[canonical_norm] = code

                existing_names = code_to_names.get(code)
                if existing_names is not None and existing_names != (canonical, aliases):
                    raise ValueError(
                        "Code collision: "
                        f"{code} maps to both {existing_names} and {(canonical, aliases)}"
                    )
                code_to_names[code] = (canonical, aliases)

                # Allow searching by canonical key as an alias.
                alias_to_code[canonical_norm] = code

                for alias in aliases:
                    alias_norm = _normalize(alias)
                    existing = alias_to_code.get(alias_norm)
                    if existing is not None and existing != code:
                        raise ValueError(
                            "Alias collision: " f"{alias!r} maps to both {existing} and {code}"
                        )
                    alias_to_code[alias_norm] = code

        self.alias_to_code = MappingProxyType(alias_to_code)
        self.canonical_to_code = MappingProxyType(canonical_to_code)
        self.code_to_names = MappingProxyType(code_to_names)

        # Keep header consistent even if the collection was mutated in a way that
        # bypassed our change hooks.
        self._refresh_header_from_collection()
        self.collection.mark_clean()

    def _ensure_indexes(self) -> None:
        if self.collection.is_dirty:
            self._rebuild_indexes()

    def get_full_code(
        self,
        alias: str,
        *,
        canonical_only: bool = False,
        default: FullCode | None = None,
    ) -> FullCode:
        """Resolve an input alias to a FullCode.

        If `canonical_only=True`, only canonical keys are accepted.
        If `default` is provided, missing entries return it; otherwise raises KeyError.
        """
        self._ensure_indexes()
        key = _normalize(alias)
        table = self.canonical_to_code if canonical_only else self.alias_to_code
        if default is not None:
            return table.get(key, default)
        return table[key]

    def get_aliases(
        self,
        code: FullCode,
        *,
        default: tuple[CanonicalStrKey, StringAliases] | None = None,
    ) -> tuple[CanonicalStrKey, StringAliases]:
        """Reverse lookup: given a `FullCode`, return (canonical_key, aliases)."""
        self._ensure_indexes()
        if default is not None:
            return self.code_to_names.get(code, default)
        return self.code_to_names[code]

    FullCodeIndex = int
    ValueToFilterBy = int
    def get_filtered_collection(
        self,
        criteria: dict[FullCodeIndex, set[ValueToFilterBy]]
    ) -> Iterable[AliasMappedFullCode]:
        """Table slicing function
        
        Similar to how Excel or Pandas allows filtering rows based on column values,
        this function allows filtering the collection based on both which FullCode tuple
        index (or indices) to constrain by as well as the values therein to filter by.

        FullCode = tuple[PrimaryCodeInt, SecondaryCodeInt, TertiaryCodeInt]
        where FullCodeIndex is 0 for PrimaryCodeInt, 1 for SecondaryCodeInt, and 2 for TertiaryCodeInt.

        In criteria, the keys are FullCodeIndex values (0, 1, or 2) and the values are sets of
        ValueToFilterBy integers to filter by.
        """
        # First validate FullCodeIndex keys
        for index in criteria.keys():
            if index < 0 or index > 2:
                raise ValueError(f"FullCodeIndex must be 0, 1, or 2; got {index}")
        
        self._ensure_indexes()
        filtered_collection: Iterable[AliasMappedFullCode] = []

        # Values to filter by should not be strict. Thus if ValueToFilterBy does not exist in the index of the FullCode
        # tuple, we'll ignore that constraint.
        for alias_map, code in self.collection:
            match = True
            for index, values in criteria.items():
                if code[index] not in values:
                    match = False
                    break
            if match:
                filtered_collection.append((alias_map, code))        

        return filtered_collection
    
    def add_custom_entry(
        self,
        alias_map: Mapping[CanonicalStrKey, StringAliases],
        full_code: FullCode,
    ) -> None:
        """Add a new entry to the collection.

        Args:
            alias_map: Mapping of canonical keys to their aliases.
            full_code: A 3-tuple full code.
        """
        if self.mutability == MutabilityLevel.COMBINED:
            raise RuntimeError("Cannot modify a COMBINED collection.")
        if self.mutability == MutabilityLevel.DEFAULT:
            raise RuntimeError("Cannot modify a DEFAULT collection.")

        self.collection.append((alias_map, full_code))
        