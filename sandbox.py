from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from enum import Enum, auto
from pprint import pprint
from timeit import timeit
from typing import NamedTuple, Union

import pandas as pd
from pympler import asizeof
from typing_extensions import TypeAlias

from components.data import CharacteristicCode, KnowledgeCode, Primitive, SkillCode
from components.definitions import (
    ComponentClassInfo,
    _collect_module_classes,
)
from humaniseT5.definitions import (
    _convert_comma_delimited_str_to_tuple,
    _convert_type_to_str_name,
)

PrimitiveTypes: TypeAlias = Union[int, float, bool]
Signature: TypeAlias = tuple[PrimitiveTypes, ...]

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]

Class: TypeAlias = type

DEFINITIONS_XLSX_PATH = r"D:\Projects\Python\Sophont\humaniseT5\definitions\Definitions.xlsx"

classes = _collect_module_classes("components.data", (Primitive,))


class ComponentAttributeInfo(NamedTuple):
    name: str
    signature: tuple[PrimitiveTypes, ...]


class LookupWith(Enum):
    SIGNATURE = auto()
    ALIAS = auto()


# Type aliases for the two index shapes inside the definitions dict.
BySignature: TypeAlias = OrderedDict[tuple[Class, ComponentAttributeInfo], AliasMap]
"""Forward index: (class, attribute info) → alias map."""

ByAlias: TypeAlias = OrderedDict[tuple[Class, str], ComponentAttributeInfo]
"""Reverse index: (class, canonical-or-alias string) → attribute info."""

DefinitionsIndex: TypeAlias = OrderedDict["LookupWith", "BySignature | ByAlias"]


# ---------------------------------------------------------------------------
# fetch_definitions
# ---------------------------------------------------------------------------


def fetch_definitions(
    classes: dict[type, ComponentClassInfo],
    language: str = "en",
) -> DefinitionsIndex:
    """Build forward (signature → names) and reverse (name → attribute)
    indices from the Definitions workbook, in a single pass per sheet.
    """

    # Read every sheet once -------------------------------------------------
    data: dict[str, pd.DataFrame] = pd.read_excel(
        DEFINITIONS_XLSX_PATH, sheet_name=None, engine="openpyxl"
    )

    # Map sheet-base (before first '.') → list of sheet names ---------------
    base_map: dict[str, list[str]] = {}
    for sheet_name in data:
        base_map.setdefault(sheet_name.split(".", 1)[0], []).append(sheet_name)

    # Indices built in one pass ---------------------------------------------
    by_signature: BySignature = OrderedDict()
    by_alias: ByAlias = OrderedDict()

    for domain in classes:
        domain_name = _convert_type_to_str_name(domain)
        matches = base_map.get(domain_name)
        if not matches:
            print(f"Warning: No sheets for domain '{domain_name}'.")
            continue

        # Classify sheets: skip the bare master sheet; process all dotted ones.
        for sheet in matches:
            if sheet == domain_name:
                continue  # master sheet — no row data to index
            suffix = sheet.split(".", 1)[1]
            # suffix is either "signature" or a field name like "upp_position"
            attr_name = suffix
            value_col = "signature" if suffix == "signature" else suffix

            df = data[sheet]
            for _, row in df.iterrows():
                if row.get("lang") != language:
                    continue
                canonical = row.get("canonical")
                if canonical is None:
                    continue

                sig_tuple = _convert_comma_delimited_str_to_tuple(row.get(value_col), type=int)
                aliases = _convert_comma_delimited_str_to_tuple(row.get("aliases"), type=str)
                attribute = ComponentAttributeInfo(name=attr_name, signature=sig_tuple)
                alias_map: AliasMap = {canonical: aliases}

                # Forward index: (class, attribute) → alias map
                by_signature[(domain, attribute)] = alias_map

                # Reverse index: every known string → attribute
                by_alias[(domain, canonical)] = attribute
                for alias in aliases:
                    if alias:  # guard against empty strings
                        by_alias[(domain, alias)] = attribute

    return OrderedDict(
        [
            (LookupWith.SIGNATURE, by_signature),
            (LookupWith.ALIAS, by_alias),
        ]
    )


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_alias_map_by_signature(
    index: DefinitionsIndex,
    cls: type,
    sig: Signature,
) -> AliasMap | None:
    """O(1) forward lookup: class + value-signature → alias map."""
    key = (cls, ComponentAttributeInfo(name="signature", signature=sig))
    sig_index = index[LookupWith.SIGNATURE]  # type: ignore[assignment]
    return sig_index.get(key)  # type: ignore[call-arg]


def get_attribute_by_name(
    index: DefinitionsIndex,
    cls: type,
    name: str,
) -> ComponentAttributeInfo | None:
    """O(1) reverse lookup: class + canonical-or-alias string → attribute info."""
    """O(1) reverse lookup: class + canonical-or-alias string → attribute info."""
    alias_index: ByAlias = index[LookupWith.ALIAS]  # type: ignore[assignment]
    return alias_index.get((cls, name))


# ---------------------------------------------------------------------------
# Timing / diagnostics
# ---------------------------------------------------------------------------

file_read_time = (
    timeit(
        lambda: pd.read_excel(DEFINITIONS_XLSX_PATH, sheet_name=None),
        number=1,
    )
    * 1000
)
fetch_definitions_time = timeit(lambda: fetch_definitions(classes), number=1) * 1000
pprint(f"Read excel file time: {file_read_time:.2f} ms")
pprint(
    f"Fetch definitions time - Reading Excel File: "
    f"{(fetch_definitions_time - file_read_time):.2f} ms"
)
pprint(f"Fetch definitions time - Total: {fetch_definitions_time:.2f} ms")
definitions = fetch_definitions(classes)
pprint(f"asizeof.asizeof(definitions): {asizeof.asizeof(definitions) / 1024:.2f} kb")

# ── Test forward lookup (signature → aliases) ────────────────────────
print("\n── Forward lookup (signature → aliases) ──")
test_signatures: list[tuple[type, Signature, str]] = [
    (KnowledgeCode, (12, -99, 37, 2, -99), "KnowledgeCode"),
    (CharacteristicCode, (1, 0, 1), "CharacteristicCode"),
    (SkillCode, (25, 1, -99), "SkillCode"),
]

for cls, sig, label in test_signatures:
    result = get_alias_map_by_signature(definitions, cls, sig)
    if result is None:
        print(f"  {label} {sig}  →  NOT FOUND")
    else:
        for canon, aliases in result.items():
            print(f"  {label} {sig}  →  canonical={canon!r}, aliases={aliases}")

# ── Test reverse lookup (canonical / alias → attribute) ──────────────
print("\n── Reverse lookup (name → attribute) ──")
test_names: list[tuple[type, str, str]] = [
    (CharacteristicCode, "strength", "CharacteristicCode"),
    (CharacteristicCode, "str", "CharacteristicCode (alias)"),
    (SkillCode, "language", "SkillCode"),
    (KnowledgeCode, "sophontology", "KnowledgeCode"),
    (CharacteristicCode, "nonexistent", "CharacteristicCode (miss)"),
]

for cls, name, label in test_names:
    attr = get_attribute_by_name(definitions, cls, name)
    if attr is None:
        print(f"  {label} {name!r}  →  NOT FOUND")
    else:
        print(f"  {label} {name!r}  →  {attr}")
