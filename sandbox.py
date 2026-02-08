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

index_by_signature = OrderedDict[LookupWith.SIGNATURE, OrderedDict[tuple[Class, ComponentAttributeInfo], AliasMap]] 
"""Flat index of all components and their attributes, keyed by 
lookup method signature → (class, attribute info) → alias map.
"""
index_by_alias = OrderedDict[LookupWith.ALIAS, OrderedDict[tuple[Class, AliasMap], ComponentAttributeInfo]]
"""Flat index of all components and their attributes, keyed by
lookup method alias → (class, alias map) → attribute info."""

def fetch_definitions(
        classes: dict[type, ComponentClassInfo], 
        language: str = "en"
        ) -> index_by_signature:
    
    # --------------------------------------------------------------------------- 
    # Read excel file once for all the data required to build the index, rather than reading it multiple times for each domain.
    # ---------------------------------------------------------------------------
    data = pd.read_excel(DEFINITIONS_XLSX_PATH, sheet_name=None, engine="openpyxl") # dict of DataFrames keyed by sheet name


    # --------------------------------------------------------------------------- 
    # Map the available data from the excel file
    # ---------------------------------------------------------------------------
     
    # Build a one-pass mapping from the sheet base (before first '.') -> list of sheet names.
    # This avoids scanning the entire DataFrame for every domain (avoids O(D*N)).
    base_map: OrderedDict[str, list[str]] = OrderedDict()
    for s in data.keys():
        base = s.split(".", 1)[0]
        base_map.setdefault(base, []).append(s)

    # --------------------------------------------------------------------------- 
    # Apply the definitions to the collected classes, building the final index structure.
    # ---------------------------------------------------------------------------

    definitions_by_signature: OrderedDict[tuple[Class, ComponentAttributeInfo], AliasMap] = OrderedDict()
    for domain in classes.keys():
        matches = base_map.get(_convert_type_to_str_name(domain))
        # Master sheets are those that match the domain name exactly (e.g. "CharacteristicCode" for the CharacteristicCode class).
        # Signature sheets are those that end with ".signature" (e.g. "CharacteristicCode.signature").
        # Field sheets are those that match the pattern "{Domain}.{FieldName}" (e.g. "CharacteristicCode.upp_position").
        if not matches:
            print(f"Warning: No sheets found for domain '{domain}' (searched for base '{_convert_type_to_str_name(domain)}').")
            continue
        master_sheets = next((s for s in matches if s == _convert_type_to_str_name(domain)), None)
        signature_sheets = next((s for s in matches if s.endswith(".signature")), None)
        field_sheets = [s for s in matches if s not in (master_sheets, signature_sheets)]
        
        # For signature and field sheets, we expect columns: 'lang', 'canonical', 'aliases'
        for signature_sheet in [signature_sheets]:
            if not signature_sheet:
                continue
            df = data[signature_sheet]
            for _, row in df.iterrows():
                signature = row.get("signature")
                lang = row.get("lang")
                canonical = row.get("canonical")
                aliases = row.get("aliases")
                if lang == language and canonical is not None:
                    attribute: ComponentAttributeInfo = ComponentAttributeInfo(
                        name="signature",
                        signature=_convert_comma_delimited_str_to_tuple(signature, type=int)
                    )
                    definitions_by_signature[(domain, attribute)] = {canonical: _convert_comma_delimited_str_to_tuple(aliases, type=str)}
        
        for field_sheet in field_sheets:
            if not field_sheet:
                continue
            df = data[field_sheet]
            for _, row in df.iterrows():
                field_name = field_sheet.split(".", 1)[1]
                signature = row.get(field_name)
                lang = row.get("lang")
                canonical = row.get("canonical")
                aliases = row.get("aliases")
                if lang == language and canonical is not None:
                    attribute: ComponentAttributeInfo = ComponentAttributeInfo(
                        name=field_name,
                        signature=_convert_comma_delimited_str_to_tuple(signature, type=int)
                    )
                    definitions_by_signature[domain, attribute] = {canonical: _convert_comma_delimited_str_to_tuple(aliases, type=str)}

    definitions = OrderedDict([(LookupWith.SIGNATURE, definitions_by_signature)])

    # --------------------------------------------------------------------------- 
    # PLACEHOLDER: Transform into LookupWith(Enum) flat structures
    # ---------------------------------------------------------------------------
     
    
    return definitions

file_read_time = timeit(lambda: pd.read_excel(DEFINITIONS_XLSX_PATH, sheet_name=None), number=1)*1000
fetch_definitions_time = timeit(lambda: fetch_definitions(classes), number=1)*1000
pprint(f"Read excel file time: {file_read_time:.2f} ms")
pprint(f"Fetch definitions time - Reading Excel File: {(fetch_definitions_time - file_read_time):.2f} ms")
pprint(f"Fetch definitions time - Total: {fetch_definitions_time:.2f} ms")
definitions = fetch_definitions(classes)
pprint(f"asizeof.asizeof(definitions): {asizeof.asizeof(definitions)/1024:.2f} kb")

# ── Test signatures ───────────────────────────────────────────────────
test_cases: list[tuple[type, Signature, str]] = [
    (KnowledgeCode, (12, -99, 37, 2, -99), "KnowledgeCode"),
    (CharacteristicCode, (1, 0, 1), "CharacteristicCode"),
    (SkillCode, (25, 1, -99), "SkillCode"),
]

def get_alias_map_indexed(
    index: index_by_signature,
    cls: type,
    sig: Signature,
) -> AliasMap | None:
    """O(1) lookup against a pre-built index.

    TRAVERSAL STEPS
    ────────────────
    1. Construct the composite key `(cls, sig)`.
    2. Single dict `.get()` call — Python hashes the tuple, probes
       the hash table, and returns the value (or None).
       No iteration, no inner-dict descent.  That work was already
       done when the index was built.
    """
    component = ComponentAttributeInfo(name="signature", signature=sig)
    return index[LookupWith.SIGNATURE].get((cls, component))

for cls, sig, label in test_cases:
        result = get_alias_map_indexed(definitions, cls, sig)
        if result is None:
            print(f"  {label} {sig}  →  NOT FOUND")
        else:
            for canon, aliases in result.items():
                print(f"  {label} {sig}  →  canonical={canon!r}, aliases={aliases}")