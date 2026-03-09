from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any, NamedTuple

import pandas as pd
from typing_extensions import TypeAlias

from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import AuthoredValue, Converters, ConvertersType
from utils.semantics import (
    convert_bytes_to_tuple,
    convert_to_bytes,
    generate_signature_oop,
    nested_tuple_to_nested_list,
    signature_transformer,
    split_flattened_aliases,
)

"""
See _prototypes.t5_api_semantics_extraction.py
"""
# region SETUP
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                                SETUP ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

Signature: TypeAlias = bytes
FlattenedAliasMap: TypeAlias = str
SearchHeader: TypeAlias = dict[str, list[str]]

BySignature: TypeAlias = dict[Signature, FlattenedAliasMap]
"""Forward index: Signature → FlattenedAliasMap."""

ByAliasForSignature: TypeAlias = dict[tuple[int, FlattenedAliasMap], Signature]
"""Reverse index: (domain_identity, FlattenedAliasMap) → Signature."""

ByMemberIdentity: TypeAlias = dict[tuple[int, int, int], FlattenedAliasMap]
"""Member index: (domain_identity, member_identity, value) → FlattenedAliasMap."""

ByAliasForMemberIdentity: TypeAlias = dict[tuple[int, int, FlattenedAliasMap], int]
"""Reverse member index: (domain_identity, member_identity, FlattenedAliasMap) → value."""
# endregion

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                   PANDAS CONVERTERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
converters: ConvertersType = {
    "signature": Converters.tuple_int,
    "canonical": Converters.to_str,
    "aliases": Converters.list_str,
    "associated_skill": Converters.tuple_int,
}

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                  DEFINITIONS INDICES ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


class DefinitionsIndices(NamedTuple):
    """Immutable container holding multiple lookup indices built from the
    Definitions workbook.  Lookup helpers accept this as a single
    ``search_index`` argument and internally select the correct
    sub-index."""

    by_header: MappingProxyType = MappingProxyType(SearchHeader({}))
    by_signature: MappingProxyType = MappingProxyType(BySignature({}))
    by_alias_for_signature: MappingProxyType = MappingProxyType(ByAliasForSignature({}))
    by_member_identity: MappingProxyType = MappingProxyType(ByMemberIdentity({}))
    by_alias_for_member_identity: MappingProxyType = MappingProxyType(ByAliasForMemberIdentity({}))


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                               BUILD INDICES HELPERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


def _generate_base_and_header_maps(
    classes: list[type],
    sheet_names: list[str],
) -> tuple[dict[type, list[str]], dict[type, list[str]]]:
    """Build base_map (cls → sheet names) and header_map (cls → available
    member sheet names) in a single pass over *classes*."""

    base_map: dict[type, list[str]] = {}
    header_map: dict[type, list[str]] = {}

    for component_cls in classes:
        prefix = component_cls.__name__ + "."
        base_map[component_cls] = [s for s in sheet_names if s.startswith(prefix)]

    # Flatten all base-map sheet names into a set once for O(1) membership tests.
    all_sheet_members: set[str] = {s for sheets in base_map.values() for s in sheets}

    for component_cls in classes:
        members = component_cls.semantic_map.members
        header_map[component_cls] = [name for (name, _) in members if name in all_sheet_members]

    return base_map, header_map


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                       BUILD INDICES ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


def build_definitions_indices(
    classes: list[type],
    language: str = "en",
) -> DefinitionsIndices:
    """Read the Definitions workbook and return populated lookup indices."""

    data: dict[str, pd.DataFrame] = pd.read_excel(
        DEFINITIONS_XLSX_PATH,
        sheet_name=None,
        engine="openpyxl",
        converters=converters,
    )

    base_map, header_map = _generate_base_and_header_maps(classes, sheet_names=list(data.keys()))

    by_signature: BySignature = {}
    by_member_identity: ByMemberIdentity = {}
    by_alias_for_signature: ByAliasForSignature = {}
    by_alias_for_member_identity: ByAliasForMemberIdentity = {}

    for component_cls, sheets in base_map.items():
        domain_identity = component_cls.subclass_dict.get(component_cls)

        # Pre-build suffix → member_identity lookup for this class.
        member_map = component_cls.semantic_map.members
        cls_prefix = component_cls.__name__ + "."
        suffix_to_member_id: dict[str, int] = {}
        for (name, _), mid in member_map.items():
            if name.startswith(cls_prefix):
                suffix_to_member_id[name[len(cls_prefix) :]] = mid

        for sheet in sheets:
            suffix = sheet.split(".", 1)[1]

            required_cols = {suffix, "lang", "canonical", "aliases"}
            missing = required_cols - set(data[sheet].columns)
            if missing:
                raise ValueError(
                    f"Expected column(s) {sorted(missing)} not found in sheet '{sheet}'"
                )

            # Pre-filter to target language — avoids per-row branch.
            df_lang = data[sheet][data[sheet]["lang"] == language]

            for row in df_lang.itertuples(index=False):
                authored_value = getattr(row, suffix)
                canonical: AuthoredValue = row.canonical
                aliases: AuthoredValue = row.aliases
                flattened_aliases = ",".join([canonical.value] + aliases.value)

                if suffix == "signature":
                    component_signature = generate_signature_oop(
                        component_cls.semantic_map, authored_value.value
                    )
                    by_signature[component_signature] = flattened_aliases
                    by_alias_for_signature[(domain_identity, flattened_aliases)] = (
                        component_signature
                    )
                else:
                    member_identity = suffix_to_member_id[suffix]
                    by_member_identity[(domain_identity, member_identity, authored_value)] = (
                        flattened_aliases
                    )
                    by_alias_for_member_identity[
                        (domain_identity, member_identity, flattened_aliases)
                    ] = authored_value

    return DefinitionsIndices(
        by_header=MappingProxyType(header_map),
        by_signature=MappingProxyType(by_signature),
        by_alias_for_signature=MappingProxyType(by_alias_for_signature),
        by_member_identity=MappingProxyType(by_member_identity),
        by_alias_for_member_identity=MappingProxyType(by_alias_for_member_identity),
    )


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      SEMANTIC SEARCH ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


def get_primitive_semantics_from_instance(
    instance: Any,
    definitions: DefinitionsIndices,
    classes: list[type],
) -> dict[type, dict[tuple[int, str] | str, Any]]:  # SemanticInfo
    """Return human-readable semantics for a component *instance* by
    resolving its signature and per-member values against *definitions*."""

    # -- reverse-lookup dicts built once per call --------------------------------
    identity_to_cls: dict[int, type] = {cls.subclass_dict.get(cls): cls for cls in classes}
    name_to_cls: dict[str, type] = {cls.__name__: cls for cls in classes}

    # -- transform semantic signature into per-component items -------------------
    semantic_signature_array = nested_tuple_to_nested_list(instance.semantic_signature)
    elements = instance.semantic_map.elements
    array_transform_pattern = [[depth, domain_id, count] for depth, domain_id, count in elements]

    transformed_signature = signature_transformer(semantic_signature_array, array_transform_pattern)

    # -- resolve each component's full signature ---------------------------------
    signature_semantics: dict[type, dict[tuple[int, str] | str, Any]] = {}

    for item in transformed_signature:
        component_cls = identity_to_cls.get(item[0])
        if component_cls is None:
            raise KeyError(f"Unknown component identity: {item[0]}")

        signature_bytes = convert_to_bytes(item)
        canonical, *alias_list = split_flattened_aliases(
            definitions.by_signature.get(signature_bytes)
        )
        signature_semantics[component_cls] = {
            "canonical": canonical,
            "aliases": alias_list,
        }

    # -- resolve per-member values for the root component ------------------------
    component_signature = convert_bytes_to_tuple(instance.component_signature)

    first_component_cls: type = next(iter(signature_semantics))
    available_headers = definitions.by_header.get(first_component_cls)
    semantic_members = first_component_cls.semantic_map.members

    members: dict[tuple[str, type], int] = {}
    for (member_name, _), member_identity in semantic_members.items():
        if member_name in available_headers:
            member_cls = name_to_cls.get(member_name.split(".", 1)[0])
            if member_cls is not None:
                members[(member_name, member_cls)] = member_identity

    for (member_name, member_cls), member_identity in members.items():
        cls_identity = member_cls.subclass_dict.get(member_cls)
        member_value = component_signature[member_identity + 1]
        member_canonical, *member_alias_list = split_flattened_aliases(
            definitions.by_member_identity.get((cls_identity, member_identity, member_value))
        )
        signature_semantics[member_cls][(member_identity, member_name)] = {
            # "member": member_identity,
            "value": member_value,
            "canonical": member_canonical,
            "aliases": member_alias_list,
        }

    return signature_semantics
