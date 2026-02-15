from __future__ import annotations

from collections import OrderedDict, namedtuple
from collections.abc import Mapping
from typing import Any, NamedTuple, Union

import pandas as pd
from typing_extensions import TypeAlias

from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import (
    convert_comma_delimited_str_to_tuple,
    convert_type_to_str_name,
    lowercase_and_strip,
)

PrimitiveTypes = namedtuple("Primitives", ["int", "float", "bool"])(int, float, bool)
UnionPrimitiveTypes: TypeAlias = Union[int, float, bool]
Signature: TypeAlias = tuple[Any, ...]

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]
FlattenedAliasMap: TypeAlias = str

Class: TypeAlias = int
"""Instead of using the actual class objects as keys in the indices, 
we use their unique integer identities from their subclass_dict. 
This is for a tighter coupling with a DOTS architecture."""


class ComponentAttributeInfo(NamedTuple):
    name: str
    """Name of the attribute, e.g. 'subtype' in CharacteristicCode."""
    signature: Signature
    """The attribute's signature, i.e. the flattened tuple of primitive types"""


class ComponentClassInfo(NamedTuple):
    """Collected metadata for a single component class."""

    signature: tuple[type, ...]
    """Flattened primitive-type tuple (from the class's ``Signature`` ClassVar)."""
    fields: dict[str, type]
    """Insertion-ordered mapping of field name → resolved type."""


# Type aliases for the two index shapes inside the definitions dict.
BySignature: TypeAlias = OrderedDict[Signature, AliasMap]
"""Forward index: (class, attribute info) → alias map."""

ByAlias: TypeAlias = OrderedDict[tuple[Class, FlattenedAliasMap], Signature]
"""Reverse index: (class, canonical-or-alias string) → attribute info."""


class DefinitionsIndex(NamedTuple):
    """Immutable container holding both lookup indices built from the
    Definitions workbook.  Lookup helpers accept this as a single
    ``search_index`` argument and internally select the correct
    sub-index."""

    by_signature: BySignature
    """Forward index: (class, ComponentAttributeInfo) → AliasMap."""
    by_alias: ByAlias
    """Reverse index: (class, canonical-or-alias string) → ComponentAttributeInfo."""


# ---------------------------------------------------------------------------
# fetch_definitions
# ---------------------------------------------------------------------------


def fetch_definitions(
    classes: dict[type, ComponentClassInfo],
    language: str = "en",
) -> Any:
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
        domain_identity = domain.subclass_dict.get(domain.__name__)
        signature = domain.signature
        # print(f"Domain Identity for {domain.__class__.__name__}:", domain_identity)
        domain_name = convert_type_to_str_name(domain)
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

                sig_tuple = convert_comma_delimited_str_to_tuple(row.get(value_col), type=int)
                aliases = convert_comma_delimited_str_to_tuple(row.get("aliases"), type=str)
                attribute = ComponentAttributeInfo(name=attr_name, signature=sig_tuple)
                alias_map: AliasMap = {canonical: aliases}

                # Forward index: (class, attribute) → alias map
                by_signature[signature] = alias_map

                # Reverse index: every known string → attribute
                by_alias[(domain_identity, canonical)] = signature
                for alias in aliases:
                    if alias:  # guard against empty strings
                        by_alias[(domain_identity, alias)] = signature

    return DefinitionsIndex(by_signature=by_signature, by_alias=by_alias)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_alias_map_by_signature(
    cls: type,
    sig: Signature,
    search_index: DefinitionsIndex,
) -> AliasMap | None:
    """O(1) forward lookup: class + value-signature → alias map."""
    domain_identity = cls.subclass_dict.get(cls.__name__)
    return search_index.by_signature.get(
        (cls.signature)
    )


def get_attribute_by_name(
    cls: type,
    name: str,
    search_index: DefinitionsIndex,
) -> ComponentAttributeInfo | None:
    """O(1) reverse lookup: class + canonical-or-alias string → attribute info."""
    domain_identity = cls.subclass_dict.get(cls.__name__)
    name = lowercase_and_strip(name)
    return search_index.by_alias.get((domain_identity, name))
