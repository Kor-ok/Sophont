from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from types import MappingProxyType
from typing import Any, Final

from game.mappings.utils import AttributeViewHeader, _normalize


class MutabilityLevel(Enum):
    DEFAULT = "default"
    CUSTOM = "custom"
    COMBINED = "combined"


CanonicalStrKey = str
StringAliases = tuple[str, ...]
AliasMap = Mapping[CanonicalStrKey, StringAliases]
FullCode = tuple[int, int, int]

AliasMappedFullCode = tuple[AliasMap, FullCode]

# Shape of the Data:
# - AliasMap: { canonical_key: (alias1, alias2, ...) }
# - FullCode: (int, int, int)
# - Entry: (AliasMap, FullCode)


def _is_full_code(value: object) -> bool:
    if not isinstance(value, tuple) or len(value) != 3:
        return False
    return all(isinstance(x, int) for x in value)


# def _normalize_alias(text: str) -> str:
#     # casefold is generally better than lower for user-input comparisons.
#     return text.strip().casefold()


class DirtyCollection(list[AliasMappedFullCode]):
    """A list-like collection that tracks if it has been modified."""

    __slots__ = ("is_dirty", "version")

    def __init__(self, iterable: Iterable[AliasMappedFullCode] = ()) -> None:
        super().__init__(iterable)
        self.is_dirty: bool = False
        self.version: int = 0

    def _bump(self) -> None:
        self.is_dirty = True
        self.version += 1

    def mark_clean(self) -> None:
        self.is_dirty = False

    def append(self, __object: AliasMappedFullCode) -> None:  # type: ignore[override]
        self._bump()
        super().append(__object)

    def extend(self, __iterable: Iterable[AliasMappedFullCode]) -> None:  # type: ignore[override]
        self._bump()
        super().extend(__iterable)

    def insert(self, __index: int, __object: AliasMappedFullCode) -> None:  # type: ignore[override]
        self._bump()
        super().insert(__index, __object)

    def remove(self, __value: AliasMappedFullCode) -> None:  # type: ignore[override]
        self._bump()
        super().remove(__value)

    def pop(self, __index: int = -1) -> AliasMappedFullCode:  # type: ignore[override]
        self._bump()
        return super().pop(__index)

    def clear(self) -> None:  # type: ignore[override]
        self._bump()
        super().clear()

    def __setitem__(self, key: int | slice, value: Any) -> None:  # type: ignore[override]
        self._bump()
        super().__setitem__(key, value)

    def __delitem__(self, key: int | slice) -> None:  # type: ignore[override]
        self._bump()
        super().__delitem__(key)

    def __iadd__(self, other: Iterable[AliasMappedFullCode]) -> DirtyCollection:  # type: ignore[override]
        self._bump()
        return super().__iadd__(other)

    def __imul__(self, n: int) -> DirtyCollection:  # type: ignore[override]
        self._bump()
        return super().__imul__(n)


class AliasMappedFullCodeCollection:
    mutability: MutabilityLevel
    collection: DirtyCollection
    header: AttributeViewHeader

    alias_to_code: Mapping[str, FullCode]
    canonical_to_code: Mapping[str, FullCode]
    code_to_names: Mapping[FullCode, tuple[CanonicalStrKey, StringAliases]]

    __slots__ = (
        "mutability",
        "collection",
        "header",
        "alias_to_code",
        "canonical_to_code",
        "code_to_names",
    )

    _EMPTY: Final[Mapping[Any, Any]] = MappingProxyType({})

    def __init__(
        self,
        *,
        mutability: MutabilityLevel,
        collection: Iterable[AliasMappedFullCode] = (),
        header: AttributeViewHeader | None = None,
    ) -> None:
        self.mutability = mutability
        self.collection = DirtyCollection(collection)
        self.header = header if header is not None else AttributeViewHeader()

        self.alias_to_code = self._EMPTY  # type: ignore[assignment]
        self.canonical_to_code = self._EMPTY  # type: ignore[assignment]
        self.code_to_names = self._EMPTY  # type: ignore[assignment]

        # Ensure first query builds indexes.
        self.collection.is_dirty = True

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
