from __future__ import annotations

from collections.abc import Iterable  # noqa: F401
from typing import Final, cast  # noqa: F401

from game.improvedmappings import (
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
    CHARACTERISTICS_MASTER_CATEGORY_CODES,  # noqa: F401
    CHARACTERISTICS_MATRIX,  # noqa: F401
)
from game.improvedmappings.attributes import AttributesBase
from game.improvedmappings.utils import AttributeViewHeader, _normalize

StringAliases = tuple[str, ...]

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCharacteristicCodeTuple = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]

StrCodeStr = str 
CanonicalAlias = str

class Characteristics(AttributesBase):
    """
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES: Final[dict[tuple[FullCharacteristicCodeTuple, StrCodeStr], StringAliases]]
    FullCharacteristicCodeTuple = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
    """
    __slots__ = (
        "custom_characteristic_master_category_name_aliases_dict",
        "custom_characteristic_code_name_aliases_dict",
    )
    
    def __init__(self) -> None:
        object.__setattr__(self, "custom_characteristic_master_category_name_aliases_dict", dict[int, StringAliases]())
        object.__setattr__(self, "custom_characteristic_code_name_aliases_dict", dict[FullCharacteristicCodeTuple, StringAliases]())
        
        super().__init__()

    def _initialise_defaults(self) -> None:
        self.default_view_header: AttributeViewHeader # to advertise the characteristic code-space.
        # CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES: Final[dict[tuple[FullCharacteristicCodeTuple, StrCodeStr], StringAliases]]
        # FullCharacteristicCodeTuple = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
        # primary_code = UPPIndexInt
        # secondary_code = SubCodeInt

        max_upp_index = 0
        max_sub_code = 0
        max_master_code = 0
        for (full_code_tuple, str_code), aliases in CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES.items():
            upp_index, sub_code, master_code = full_code_tuple
            max_upp_index = max(max_upp_index, upp_index)
            max_sub_code = max(max_sub_code, sub_code)
            max_master_code = max(max_master_code, master_code)
            for alias in aliases:
                norm_alias = _normalize(str_code)
                self.default_canonical_alias_strkey_to_code[norm_alias] = full_code_tuple

        self.default_view_header.primary_code = max_upp_index
        self.default_view_header.secondary_code = max_sub_code
        self.default_view_header.tertiary_code = max_master_code


    


