from __future__ import annotations

from collections.abc import Mapping

from game.mappings import (
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
    CHARACTERISTICS_MASTER_CATEGORY_CODES,  # noqa: F401
    CHARACTERISTICS_MATRIX,  # noqa: F401
)
from game.mappings.attributebase import AttributeBase
from game.mappings.data import AliasMappedFullCodeCollection, MutabilityLevel

StringAliases = tuple[str, ...]
CanonicalStrKey = str

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCode = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]

AliasMap = Mapping[CanonicalStrKey, StringAliases]
AliasMappedFullCode = tuple[AliasMap, FullCode]


class Characteristics(AttributeBase):
    """
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES: AliasMappedFullCode

    StringAliases = tuple[str, ...]
    CanonicalStrKey = str

    UPPIndexInt = int
    SubCodeInt = int
    MasterCodeInt = int
    AliasMap = Mapping[CanonicalStrKey, StringAliases]
    FullCode = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
    AliasMappedFullCode = tuple[AliasMap, FullCode]

    Inherits from AttributeBase:
    "default_collection", "custom_collection", "combined_collection", "_is_initialised"
    """

    __slots__ = (
        "custom_characteristic_master_category_name_aliases_dict",
        "custom_characteristic_code_name_aliases_dict",
    )
    custom_characteristic_master_category_name_aliases_dict: dict[int, StringAliases]
    custom_characteristic_code_name_aliases_dict: dict[FullCode, StringAliases]

    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.custom_characteristic_master_category_name_aliases_dict
            self.custom_characteristic_code_name_aliases_dict
        except AttributeError:
            object.__setattr__(
                self,
                "custom_characteristic_master_category_name_aliases_dict",
                dict[int, StringAliases](),
            )
            object.__setattr__(
                self,
                "custom_characteristic_code_name_aliases_dict",
                dict[FullCode, StringAliases](),
            )

        super().__init__()

    def _initialise_defaults(self) -> None:
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
            mutability=MutabilityLevel.DEFAULT,
        )
