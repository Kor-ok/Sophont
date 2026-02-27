from __future__ import annotations

import json
import logging
from types import MappingProxyType
from typing import Any, NamedTuple

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

from components.base import Primitive
from components.data import CharacteristicCode, KnowledgeCode, SkillCode, TestComplexComponent
from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import AuthoredValue, Converters, ConvertersType
from utils.semantics import (
    _bytes_to_ints,
    _expected_bytes,
    collect_module_classes,
    generate_signature_oop,
    nested_tuple_to_nested_list,
)
from utils.terminal import header

#region SETUP
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                                SETUP ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
colorama_init(autoreset=True)

DomainIdentity: TypeAlias = int
"""Instead of using the actual class objects as keys in the indices, 
we use their unique integer identities from their subclass_dict. 
This is for a tighter coupling with a DOTS architecture."""
MemberIdentity: TypeAlias = int
"""Instead of using the actual field names as keys in the indices,
we use their integer indices from the member_dict.
This is for a tighter coupling with a DOTS architecture, where we
want to avoid string lookups."""
MembersLength: TypeAlias = int
"""The number of members in a component, which is needed to know 
how many values to extract from the signature tuple for each 
component when we have multiple components recursively nested 
within each other, to be able to look up the semantics for each 
component separately."""
Signature: TypeAlias = bytes # tuple[int, ...]

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = dict[CanonicalStrKey, StringAliases]
FlattenedAliasMap: TypeAlias = str

SearchHeader: TypeAlias = dict[str, list[str]]

# Creating a single Signature tuple by adding the domain identity at the start:
BySignature: TypeAlias = dict[Signature, FlattenedAliasMap]
"""Forward index: (DomainIdentity, Signature) → FlattenedAliasMap."""

ByAliasForSignature: TypeAlias = dict[
    tuple[DomainIdentity, FlattenedAliasMap],
    Signature
]
"""Reverse index: (DomainIdentity, FlattenedAliasMap) → Signature."""

ByMemberIdentity: TypeAlias = dict[
    tuple[DomainIdentity, MemberIdentity, int],
    FlattenedAliasMap
]
"""Member index: (DomainIdentity, MemberIdentity, Signature) → FlattenedAliasMap."""

ByAliasForMemberIdentity: TypeAlias = dict[
    tuple[DomainIdentity, MemberIdentity, FlattenedAliasMap],
    int
]
"""Reverse member index: (DomainIdentity, MemberIdentity, FlattenedAliasMap) → Signature."""
#endregion

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
# ┃                                                               BUILD INDICES HELPERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
BaseMap = dict[type, list[str]]
HeaderMap = dict[type, list[str]]
Members = dict[tuple[str, type], int]
def _generate_base_and_header_maps(classes: list[type], data_frame: dict[str, pd.DataFrame]) -> tuple[BaseMap, HeaderMap]:
    base_map: BaseMap = {}
    member_maps: dict[type, Members] = {}
    header_map: HeaderMap = {}
    for component_cls in classes:
        base_map.setdefault(component_cls, [])
        for sheet_name in data_frame:
            if sheet_name.startswith(component_cls.__name__ + "."):
                member_name = sheet_name
                base_map[component_cls].append(member_name)
                
    for component_cls in classes:
        member_maps[component_cls] = component_cls.semantic_map.members

    for component_cls in classes:
        header_map.setdefault(component_cls, [])
        for member_name in member_maps[component_cls].keys():
            # If member_name[0] appears in any of the values in base_map then add member_name[0] to header_map for the component_cls key
            if member_name[0] in [member for members in base_map.values() for member in members]:
                header_map[component_cls].append(member_name[0])

    # print(f"{Fore.GREEN}Generated base map:{Style.RESET_ALL}")
    # for cls, members in base_map.items():
    #     print(f"{cls}:{Style.RESET_ALL}")
    #     for member in members:
    #         print(f"    {Fore.GREEN}{member}{Style.RESET_ALL}")

    # print(f"\n{Fore.BLUE}Generated members map:{Style.RESET_ALL}")
    # for component_cls, members in member_maps.items():
    #     print(f"{component_cls}:{Style.RESET_ALL}")
    #     for (name, type) , index in members.items():
    #         print(f"    {Fore.BLUE}{index}: {name}{Style.RESET_ALL}")

    # print(f"\n{Fore.CYAN}Generated header map:{Style.RESET_ALL}")
    # for cls, headers in header_map.items():
    #     print(f"{cls}:{Style.RESET_ALL}")
    #     for header in headers:
    #         print(f"    {Fore.CYAN}{header}{Style.RESET_ALL}")
    
    return base_map, header_map

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                       BUILD INDICES ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def build_definitions_indices(
    classes: list[type],
    language: str = "en",
) -> Any:
    
    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                                         IO ONCE ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    data: dict[str, pd.DataFrame] = pd.read_excel(
        DEFINITIONS_XLSX_PATH, sheet_name=None, engine="openpyxl", converters=converters
    )

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                  SANITISE AUTHORED WITH RUNTIME ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    base_map, header_map = _generate_base_and_header_maps(classes, data_frame=data)
    
    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                                           BUILD ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    
    by_signature: BySignature = {}
    by_member_identity: ByMemberIdentity = {}
    by_alias_for_signature: ByAliasForSignature = {}
    by_alias_for_member_identity: ByAliasForMemberIdentity = {}

    
    for component_cls, sheets in base_map.items():
        domain_identity = component_cls.subclass_dict.get(component_cls)
        # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        # ┃                                                              PROCESS SHEETS ┃
        # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        for sheet in sheets:
            # print(f"    Processing sheet: {Fore.BLUE}{sheet}...")
            suffix = sheet.split(".", 1)[1]
            # print(f"        For: {Fore.CYAN}{suffix}")
            value_col = suffix

            # Validations of column existence
            check_for_headers = [value_col, "lang", "canonical", "aliases"]
            for header in check_for_headers:  # noqa: F402
                if header not in data[sheet].columns:
                    raise ValueError(f"Expected column '{header}' not found in sheet '{sheet}'")

            df_sheet = data[sheet]
            for _, row in df_sheet.iterrows():
                if row.get("lang") != language:
                    continue
                
                authored_signature = row.get(value_col)
                # if hasattr(authored_signature, "value"):
                #     print(f"        Authored signature: {authored_signature.value}")
                # else:
                #     print(f"        Authored signature: {authored_signature}")
                canonical: AuthoredValue = row.get("canonical") # str
                # print(f"        Canonical: {canonical.value}")
                aliases: AuthoredValue = row.get("aliases") # list[str]
                # print(f"        Aliases: {aliases.value }")

                # We create a flattened alias map by joining the canonical and aliases with commas,
                flattened_aliases = ",".join([canonical.value] + aliases.value)
                # print(f"        Flattened aliases: {flattened_aliases}")
                # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                # ┃                                                        APPLY TO INDICES ┃
                # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                
                if suffix == "signature":
                    # print(f"        Processing signature sheet: {Fore.BLUE}{sheet}...")
                    component_signature = generate_signature_oop(
                        component_cls.semantic_map,
                        authored_signature.value
                        )

                    by_signature[component_signature] = flattened_aliases

                    # Reverse index: (DomainIdentity, FlattenedAliasMap) → Signature
                    by_alias_for_signature[(domain_identity, flattened_aliases)] = component_signature
                else:
                    # Member index: (DomainIdentity, MemberIdentity) → FlattenedAliasMap
                    member_map = component_cls.semantic_map.members
                    search_for = f"{component_cls.__name__}.{suffix}"
                    # print(f"Searching for {search_for}...")
                    for (name, _), member_identity in member_map.items():
                        if name == search_for:
                            by_member_identity[(domain_identity, member_identity, authored_signature)] = flattened_aliases

                            # Reverse member index: (DomainIdentity, MemberIdentity, FlattenedAliasMap) → Signature
                            by_alias_for_member_identity[(domain_identity, member_identity, flattened_aliases)] = authored_signature
                            break
                    
                
    return DefinitionsIndices(
        by_header= MappingProxyType(header_map),
        by_signature= MappingProxyType(by_signature), 
        by_alias_for_signature= MappingProxyType(by_alias_for_signature), 
        by_member_identity= MappingProxyType(by_member_identity), 
        by_alias_for_member_identity= MappingProxyType(by_alias_for_member_identity)
        )

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

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                        DEBUG HELPERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
# region DEBUG HELPERS
def display_definitions_indices(definitions: DefinitionsIndices, index_name: str | None = None, filter_by_type: type | None = None) -> None:

    domain_identity: int | None = None
    if filter_by_type is not None:
        domain_identity = next((cls.subclass_dict[filter_by_type] for cls in classes if filter_by_type in cls.subclass_dict), None)
        print(f"Filtering indices for type '{filter_by_type.__name__}'...")
        if domain_identity is None:
            raise ValueError(f"Domain identity for filter type '{filter_by_type.__name__}' not found in any of the provided classes.")

    if index_name:
        index = getattr(definitions, index_name, None)
        if index is not None:
            print(f"{Fore.GREEN}Index: {index_name}{Style.RESET_ALL}")
            for key, value in index.items():
                if domain_identity is not None and isinstance(key, tuple) and key[0] != domain_identity:
                    continue  # Skip entries that don't match the domain identity filter
                print(f"{Fore.GREEN}{key} → {value}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Index '{index_name}' not found in definitions.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Forward index (by_signature):{Style.RESET_ALL}")
        for signature, aliases in definitions.by_signature.items():
            print(f"{Fore.GREEN}{_bytes_to_ints(signature)} → {aliases}{Style.RESET_ALL}")
            # With a counter for the number of entries in the index

        print(f"\n{Fore.CYAN}Reverse index (by_alias_for_signature):{Style.RESET_ALL}")
        for (domain_identity, flattened_aliases), signature in definitions.by_alias_for_signature.items():
            print(f"{Fore.CYAN}(Domain ID: {domain_identity}, Aliases: {flattened_aliases}) → {_bytes_to_ints(signature)}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}Member index (by_member_identity):{Style.RESET_ALL}")
        for (domain_identity, member_identity, signature), aliases in definitions.by_member_identity.items():
            print(f"{Fore.BLUE}(Domain ID: {domain_identity}, Member ID: {member_identity}, Signature: {signature}) → {aliases}{Style.RESET_ALL}")

        print(f"\n{Fore.MAGENTA}Reverse member index (by_alias_for_member_identity):{Style.RESET_ALL}")
        for (domain_identity, member_identity, flattened_aliases), signature in definitions.by_alias_for_member_identity.items():
            print(f"{Fore.MAGENTA}(Domain ID: {domain_identity}, Member ID: {member_identity}, Aliases: {flattened_aliases}) → {signature}{Style.RESET_ALL}")
        
        print(f"\nTotal entries in by_signature index: {len(definitions.by_signature)}")
        print(f"Total entries in by_alias_for_signature index: {len(definitions.by_alias_for_signature)}")
        print(f"Total entries in by_member_identity index: {len(definitions.by_member_identity)}")
        print(f"Total entries in by_alias_for_member_identity index: {len(definitions.by_alias_for_member_identity)}")

def display_component_info(info: Any, colour: str = Fore.WHITE, style: str = Style.NORMAL) -> None:
    # Convert objects of non-json types throughout the deep structure
    # to their string representation for better readability in the output
    converted = {}
    def convert(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {convert(key): convert(value) for key, value in obj.items()}
        elif isinstance(obj, type) and hasattr(obj, "__name__"):
            return obj.__name__
        elif isinstance(obj, (list, tuple)):
            converted = [convert(item) for item in obj]
            # Turn into a flattened string
            converted_str = ", ".join(str(item) for item in converted)
            # Surround with [] or () depending on original type
            if isinstance(obj, list):
                converted_str = f"[{converted_str}]"
            else:
                converted_str = f"({converted_str})"
            return converted_str
        elif isinstance(obj, (int, float, str)):
            return obj
        else:
            return str(obj)
    converted = convert(info)
    print(f"{colour}{style}{json.dumps(converted, indent=4)}{Style.NORMAL}")

def display_semantic_members(members: Members, colour: str = Fore.WHITE, style: str = Style.NORMAL, padding: int = 0) -> None:
    converted = {f"{name} ({type.__name__})": index for (name, type), index in members.items()}
    print(f"{' ' * padding}{colour}{style}Semantic Members:{Style.RESET_ALL}{Style.NORMAL}")
    for member, index in converted.items():
        print(f"{' ' * padding * 2}{colour}{style}{index}: {member}{Style.RESET_ALL}{Style.NORMAL}")

def display_semantic_elements(elements: list[tuple[int, int, int]], colour: str = Fore.WHITE, style: str = Style.NORMAL, padding: int = 0) -> None:
    print(f"{' ' * padding}{colour}{style}Semantic Elements:{Style.RESET_ALL}{Style.NORMAL}")
    for depth, domain_id, count in elements:
        print(f"{' ' * padding * 2}{colour}{style}Depth: {depth}, Domain ID: {domain_id}, Count: {count}{Style.RESET_ALL}{Style.NORMAL}")
# endregion

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                              SEMANTIC SEARCH HELPERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def _split_flattened_aliases(flattened_aliases: str | None) -> tuple[str, ...]:
    if flattened_aliases is None:
        return ("UNDEFINED",)
    return tuple(alias.strip().capitalize() for alias in flattened_aliases.split(",") if alias.strip())

def signature_transformer(semantic_signature: list, semantic_mapping: list) -> list:
    # ── 1. Recursive generator — tag every atom with its nesting depth ───
    def atoms_with_depth(arr: list, depth: int = 0):
        """Yield (depth, value) for each non-list element."""
        for item in arr:
            if isinstance(item, list):
                yield from atoms_with_depth(item, depth + 1)
            else:
                yield (depth, item)

    tagged = list(atoms_with_depth(semantic_signature))

    # ── 2 hierarchical listing ─────────────────────────────────────
    
    def hierarchy(
        tagged_atoms: list[tuple[int, int]],
        pattern: list[list[int]],
    ) -> list[list[int]]:
        """Produce a hierarchical listing with embedded IDs from the pattern.

        Algorithm
        ---------
        1.  Build per-depth **consumable iterators** from the tagged stream.
            For depth *d*, the iterator yields every atom whose depth >= d,
            but resets (starts a new subtree) whenever a shallower atom is
            encountered — exactly the os.walk()-style contiguous subtree
            semantics.

        2.  Walk the ``pattern`` entries ``[depth, id, count]``.  Each step
            consumes ``count`` atoms from the iterator for that depth.
            When depth *increases* relative to the previous step, the
            ``id`` is prepended as a boundary marker.

        3.  Atoms consumed at depth *d* are appended to **every output
            row for depth <= d** (a deeper atom is part of every
            ancestor's subtree).  The ``id`` marker is likewise pushed
            into each ancestor row.

        Returns one output row per contiguous subtree, ordered by
        ascending depth level, with IDs embedded.
        """
        if not tagged_atoms:
            return []

        max_depth = max(d for d, _ in tagged_atoms)

        # ── 1. Build per-depth value pools and subtree boundaries ────
        # For each target depth, collect values (depth >= target) and
        # record where subtree breaks occur (depth < target).
        # We model each depth as a flat list with sentinel ``None``
        # values at subtree boundaries so the consumer can track which
        # subtree it is writing into.
        depth_pools: dict[int, list[int | None]] = {}
        for target_depth in range(max_depth + 1):
            pool: list[int | None] = []
            in_subtree = False
            for depth, value in tagged_atoms:
                if depth < target_depth:
                    # Surfaced above target — flush subtree boundary
                    if in_subtree:
                        pool.append(None)  # sentinel: subtree boundary
                        in_subtree = False
                elif depth == target_depth:
                    # Exact match — collect the atom
                    in_subtree = True
                    pool.append(value)
                else:
                    # Deeper than target — still inside a subtree,
                    # but don't collect (consumed via its own pool)
                    in_subtree = True
            depth_pools[target_depth] = pool

        # ── 2. Per-depth cursor + subtree-index tracking ─────────────
        depth_cursors: dict[int, int] = {d: 0 for d in depth_pools}
        # How many complete subtrees we've entered at each depth
        depth_subtree_idx: dict[int, int] = {d: 0 for d in depth_pools}

        # Output rows: one per subtree per depth level.
        # We'll collect them in a dict keyed by (depth, subtree_index).
        rows: dict[tuple[int, int], list[int]] = {}

        def _ensure_row(d: int, si: int) -> list[int]:
            if (d, si) not in rows:
                rows[(d, si)] = []
            return rows[(d, si)]

        def _consume(target_depth: int, count: int) -> list[int]:
            """Consume *count* real values from *target_depth*'s pool,
            advancing past any sentinel boundaries encountered."""
            pool = depth_pools[target_depth]
            cursor = depth_cursors[target_depth]
            values: list[int] = []
            while len(values) < count and cursor < len(pool):
                item = pool[cursor]
                cursor += 1
                if item is None:
                    # Crossed a subtree boundary
                    depth_subtree_idx[target_depth] += 1
                else:
                    values.append(item)
            depth_cursors[target_depth] = cursor
            return values

        # ── 3. Walk the pattern ──────────────────────────────────────
        prev_depth = -1
        for step_depth, step_id, step_count in pattern:
            entering_deeper = step_depth > prev_depth

            # Consume atoms from this depth's pool
            consumed = _consume(step_depth, step_count)

            # Determine the current subtree index at each level that
            # should receive these values.
            for d in range(step_depth + 1):
                si = depth_subtree_idx[d]
                row = _ensure_row(d, si)
                if entering_deeper:
                    row.append(step_id)
                row.extend(consumed)

            prev_depth = step_depth

        # ── 4. Collect rows in depth-then-subtree order ──────────────
        result: list[list[int]] = []
        for d in range(max_depth + 1):
            si = 0
            while (d, si) in rows:
                result.append(rows[(d, si)])
                si += 1

        return result
    
    result = hierarchy(tagged, semantic_mapping)
    return result

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      SEMANTIC SEARCH ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def get_semantics_from_instance(instance: Any, definitions: DefinitionsIndices) -> dict[type, dict[str, Any]]:
    """Helper function to get the semantics of a component instance using the by_signature index."""
    print(f"{Style.DIM}Semantics for '{instance}'...{Style.NORMAL}")
    print()
    
    semantic_signature = instance.semantic_signature
    semantic_signature_array = nested_tuple_to_nested_list(semantic_signature)

    semantic_map = instance.semantic_map
    semantic_elements = semantic_map.elements
    array_transform_pattern = [[depth, domain_id, count] for depth, domain_id, count in semantic_elements]

    transformed_signature = signature_transformer(semantic_signature_array, array_transform_pattern)
    # print(f"{Style.DIM}Transformed signature(s): {Style.NORMAL}{Style.RESET_ALL}")

    signature_semantics = {}

    for item in transformed_signature:
        domain_identity = item[0]
        component_cls = next((cls for cls in classes if cls.subclass_dict.get(cls) == domain_identity), None)
        signature_semantics[component_cls] = item

        # Convert the item to bytes for lookup in the by_signature index
        signature_bytes = _expected_bytes(item)
        canonical, *alias_list = _split_flattened_aliases(definitions.by_signature.get(signature_bytes))
        signature_semantics[component_cls] = {
            "component_signature": item,
            "canonical": canonical,
            "aliases": alias_list
        }
    
    # display_component_info(signature_semantics, colour=Fore.GREEN, style=Style.BRIGHT)

    first_component_cls: type = list(signature_semantics.keys())[0]
    available_headers = definitions.by_header.get(first_component_cls)
    semantic_members = first_component_cls.semantic_map.members
    
    members: dict[tuple[str, type], int] = {}
    for (member_name, _), member_identity in semantic_members.items():
        if member_name in available_headers:
            # Get the actual class from the member name by splitting on the first dot and looking up the class with that name in the classes list
            member_cls_name = member_name.split(".", 1)[0]
            member_cls = next((cls for cls in classes if cls.__name__ == member_cls_name), None)
            if member_cls is not None:
                members[(member_name, member_cls)] = member_identity 
    
    for (member_name, member_cls), member_identity in members.items():
        cls_identity = member_cls.subclass_dict.get(member_cls)
        member_value = signature_semantics[member_cls]["component_signature"][member_identity + 1]
        # print(f"{member_cls}: Class Id: {cls_identity}, Member Id: {member_identity}, Value: {member_value}")
        member_canonical, *member_alias_list  = _split_flattened_aliases(definitions.by_member_identity.get((cls_identity, member_identity, member_value)))
        # print(f"    Canonical: {member_canonical}")
        # print(f"    Aliases: {member_alias_list}")
        signature_semantics[member_cls][member_name] = {
            "member_identity": member_identity,
            "value": member_value,
            "canonical": member_canonical,
            "aliases": member_alias_list
            }
    
    # display_component_info(signature_semantics, colour=Fore.CYAN, style=Style.BRIGHT)
    return signature_semantics
         

if __name__ == "__main__":

    classes = collect_module_classes(module_name="components.data", base_classes=(Primitive,))
    definitions: DefinitionsIndices = build_definitions_indices(classes=classes)
    header("DEFINITIONS INDICES")
    # display_definitions_indices(definitions, index_name="by_signature", filter_by_type=KnowledgeCode)
    # display_definitions_indices(definitions, index_name="by_signature")
    display_definitions_indices(definitions, index_name="by_member_identity")
    # display_definitions_indices(definitions, index_name="by_header")
    # display_definitions_indices(definitions)

    initialised_components = [
        initialised_skill_code := SkillCode(key=12, set=1, group=-99),
        initialised_knowledge_code := KnowledgeCode(key=6, focus=-99, associated_skill=initialised_skill_code),
        initialised_characteristic_code := CharacteristicCode(upp_position=1, subtype=0, category=1),
        initialised_test_complex_component := TestComplexComponent(
            field1=42,
            field2=initialised_characteristic_code,
            field3=7,
            field4=3,
            field5=initialised_knowledge_code,
            field6=99
        )
    ]
    header("SEMANTICS")
    print("\n")
    for component in initialised_components:
        semantics = get_semantics_from_instance(component, definitions)
        display_component_info(semantics, colour=Fore.CYAN, style=Style.BRIGHT)
        print("\n" + "-"*80 + "\n")
