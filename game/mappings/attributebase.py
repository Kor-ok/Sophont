from __future__ import annotations

from itertools import chain
from typing import ClassVar, TypeVar

from game.mappings.data import AliasMappedFullCodeCollection, MutabilityLevel

TAttributeBase = TypeVar("TAttributeBase", bound="AttributeBase")

StringAliases = tuple[str, ...]
CanonicalStrKey = str
FullCode = tuple[int, int, int]

class AttributeBase:
    """Base Class for Skill, Knowledge, Characteristics Data.

    Handles the retrieval of default data, user-defined custom data and the collation of both
    so that all functions downstream don't need to care about the source of the data.
    """

    __slots__ = (
        "default_collection",
        "custom_collection",
        "combined_collection",
        "_is_initialised",
        "_combined_default_version",
        "_combined_custom_version",
        "_combined_default_id",
        "_combined_custom_id",
    )

    _instances: ClassVar[dict[type[AttributeBase], AttributeBase]] = {}

    def __new__(
        cls: type[TAttributeBase],
        *args: object,
        **kwargs: object,
    ) -> TAttributeBase:
        existing = AttributeBase._instances.get(cls)
        if existing is not None:
            return existing  # type: ignore[return-value]

        self = object.__new__(cls)

        object.__setattr__(
            self,
            "default_collection",
            AliasMappedFullCodeCollection(mutability=MutabilityLevel.DEFAULT, collection=()),
        )
        object.__setattr__(
            self,
            "custom_collection",
            AliasMappedFullCodeCollection(mutability=MutabilityLevel.CUSTOM, collection=()),
        )
        object.__setattr__(
            self,
            "combined_collection",
            AliasMappedFullCodeCollection(mutability=MutabilityLevel.COMBINED, collection=()),
        )
        object.__setattr__(self, "_is_initialised", False)

        object.__setattr__(self, "_combined_default_version", -1)
        object.__setattr__(self, "_combined_custom_version", -1)
        object.__setattr__(self, "_combined_default_id", 0)
        object.__setattr__(self, "_combined_custom_id", 0)
        AttributeBase._instances[cls] = self
        return self  # type: ignore[return-value]

    def __init__(self) -> None:
        if self._is_initialised:
            return
        self._initialise_defaults()
        self._ensure_combined_collection(force=True)
        object.__setattr__(self, "_is_initialised", True)

    def _combined_state(self) -> tuple[int, int, int, int]:
        return (
            id(self.default_collection),
            int(self.default_collection.collection.version),
            id(self.custom_collection),
            int(self.custom_collection.collection.version),
        )

    def _ensure_combined_collection(self, *, force: bool = False) -> None:
        default_id, default_version, custom_id, custom_version = self._combined_state()
        if not force and (
            self._combined_default_id,
            self._combined_default_version,
            self._combined_custom_id,
            self._combined_custom_version,
        ) == (default_id, default_version, custom_id, custom_version):
            return

        if not self.custom_collection.collection:
            object.__setattr__(self, "combined_collection", self.default_collection)
        else:
            combined_entries = chain(
                self.default_collection.collection,
                self.custom_collection.collection,
            )
            object.__setattr__(
                self,
                "combined_collection",
                AliasMappedFullCodeCollection.from_iterable(
                    mutability=MutabilityLevel.COMBINED,
                    entries=combined_entries,
                ),
            )

        object.__setattr__(self, "_combined_default_id", default_id)
        object.__setattr__(self, "_combined_default_version", default_version)
        object.__setattr__(self, "_combined_custom_id", custom_id)
        object.__setattr__(self, "_combined_custom_version", custom_version)

    def get_full_code(
        self,
        alias: str,
        *,
        canonical_only: bool = False,
        default: FullCode | None = None,
    ) -> FullCode:
        """Resolve an input alias to a FullCode from the combined_collection."""
        self._ensure_combined_collection()
        return self.combined_collection.get_full_code(
            alias,
            canonical_only=canonical_only,
            default=default,
        )
    
    def get_aliases(
        self,
        code: FullCode,
        *,
        default: tuple[CanonicalStrKey, StringAliases] | None = None,
    ) -> tuple[CanonicalStrKey, StringAliases]:
        """Retrieve the canonical name and aliases for a given FullCode from the combined_collection."""
        self._ensure_combined_collection()
        return self.combined_collection.get_aliases(
            code,
            default=default,
        )

    def _initialise_defaults(self) -> None:
        """Initialise the default alias to code mapping. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _initialise_defaults method.")
