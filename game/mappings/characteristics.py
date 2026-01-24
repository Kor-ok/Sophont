from __future__ import annotations

from game.mappings import (
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
    CHARACTERISTICS_MASTER_CATEGORY_CODES,  # noqa: F401
    CHARACTERISTICS_MATRIX,  # noqa: F401
)
from game.mappings.attributebase import AttributeBase
from game.mappings.data import (
    AliasMappedFullCodeCollection,
    FullCode,
    MutabilityLevel,
    StringAliases,
)


class Characteristics(AttributeBase):
    """
    
    """

    __slots__ = (
        "master_category_name_aliases_dict",
        "fullcode_to_name_aliases_dict",
    )
    master_category_name_aliases_dict: dict[int, StringAliases]
    fullcode_to_name_aliases_dict: dict[FullCode, StringAliases]

    def __init__(self) -> None:
        # AttributeBase is a per-subclass singleton; __init__ can run multiple times.
        # Only set these once to avoid wiping custom state.
        try:
            self.master_category_name_aliases_dict
            self.fullcode_to_name_aliases_dict
        except AttributeError:
            object.__setattr__(
                self,
                "master_category_name_aliases_dict",
                dict[int, StringAliases](),
            )
            object.__setattr__(
                self,
                "fullcode_to_name_aliases_dict",
                dict[FullCode, StringAliases](),
            )

        super().__init__()

    def _initialise_defaults(self) -> None:
        
        self.default_collection = AliasMappedFullCodeCollection.from_iterable(
            entries=CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
            mutability=MutabilityLevel.DEFAULT,
        )

        self.master_category_name_aliases_dict.update(CHARACTERISTICS_MASTER_CATEGORY_CODES)
