from __future__ import annotations

# from dataclasses import dataclass
from typing import Optional, Union  # Protocol

from game.gene import Gene
from game.mappings.characteristics import (
    _BASE,
    _BASE_CHAR_NAME_TO_CATEGORY_CODE,
    _SUBTYPES,
    char_name_to_category_code,
)
from game.phene import Phene


def _normalize(name: str) -> str:
    # Keep consistent with game.mappings.characteristics normalization:
    # case-insensitive + collapses repeated whitespace.
    return " ".join(str(name).strip().lower().split())


# Default item class by category.
# 1/2 are Gene-like categories; 3/4 are Phene-like categories.
DEFAULT_ITEM_TYPE_BY_CATEGORY: dict[int, Union[type[Gene], type[Phene]]] = {
    1: Gene,
    2: Gene,
    3: Phene,
    4: Phene,
}


# Exceptions to the default: force a specific item class for a characteristic name.
# Keys are normalized (case-insensitive). Values are Gene or Phene.
EXCEPTION_ITEM_TYPE_FROM_NAME: dict[str, Union[type[Gene], type[Phene]]] = {
    'education': Phene,
}


def item_type_for_characteristic_name(characteristic_name: str) -> Union[type[Gene], type[Phene]]:
    """Return the desired class (Gene/Phene) for a characteristic name.

    This applies explicit exceptions first, then falls back to category defaults.
    """
    key = _normalize(characteristic_name)
    forced = EXCEPTION_ITEM_TYPE_FROM_NAME.get(key)
    if forced is not None:
        return forced

    try:
        cat_code = char_name_to_category_code(characteristic_name)
    except Exception:
        cat_code = 0
    return DEFAULT_ITEM_TYPE_BY_CATEGORY.get(cat_code, Gene)


def generate_all_characteristics() -> list[str]:
    # _BASE_CHAR_NAME_TO_CATEGORY_CODE is characteristic name to category code
    # For each category code, get the characteristic name, then get the _BASE position code
    # and also add the subtypes based on that position code, building the list in this order
    characteristics: list[str] = []
    for cat_code in sorted(set(_BASE_CHAR_NAME_TO_CATEGORY_CODE.values())):
        for base_name, base_cat_code in _BASE_CHAR_NAME_TO_CATEGORY_CODE.items():
            if base_cat_code == cat_code:
                characteristics.append(base_name.title())
                # Get position code from base name
                pos_code = None
                for code, names in _BASE.items():
                    if names[0].lower() == base_name:
                        pos_code = code
                        break
                if pos_code is not None and pos_code in _SUBTYPES:
                    for subtype_name in _SUBTYPES[pos_code]:
                        characteristics.append(subtype_name.title())
    return characteristics

CHARACTERISTICS = generate_all_characteristics()

def build_initial_categorised_gene_and_phene_list_section(
) -> tuple[dict[int, Union[type[Gene], type[Phene]]], dict[int, list[str]]]:
    """Render the left-side list of available Genes/Phenes, grouped by category.

    Changes vs the initial implementation:
    - Precompute the list of characteristic names for each category once.
      Benefit: removes repeated nested scans over `_BASE`/`_SUBTYPES` while building UI,
      lowering the work from "scan tables every row" to O(1) dict lookups per item.
    - Use table-driven iteration (category -> names) instead of interleaving lookup logic
      with UI code.
      Benefit: cleaner control flow and easier future tweaks to categorization rules.
    """

    # Omit "Undefined" category which is key 0.
    # "Physical" = 1 and "Mental" = 2 will create Genes.
    # "Social" = 3 and "Obscure" = 4 will create Phenes.
    item_type_by_category: dict[int, Union[type[Gene], type[Phene]]] = dict(DEFAULT_ITEM_TYPE_BY_CATEGORY)

    # Build category -> [CharacteristicName, ...] (includes subtypes).
    # This used to be re-derived repeatedly inside the nested UI loops.
    characteristic_names_by_category: dict[int, list[str]] = {}
    for base_name, cat_code in _BASE_CHAR_NAME_TO_CATEGORY_CODE.items():
        characteristic_names_by_category.setdefault(cat_code, []).append(base_name.title())
        # Fast position-code lookup: `_BASE_CHAR_NAME_TO_CATEGORY_CODE` keys are canonical
        # base names, so we can find the corresponding pos_code by scanning `_BASE` once.
        # This loop runs only for the 8 base characteristics (tiny), not for every UI row.
        pos_code: Optional[int] = None
        for code, names in _BASE.items():
            if names[0].lower() == base_name:
                pos_code = code
                break
        if pos_code is None:
            continue

        subtypes = _SUBTYPES.get(pos_code)
        if subtypes:
            characteristic_names_by_category[cat_code].extend(n.title() for n in subtypes)
    
    return item_type_by_category, characteristic_names_by_category