from __future__ import annotations

import itertools as it
import json
import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, NamedTuple, get_args, get_type_hints

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

from components.base import Primitive
from components.data import CharacteristicCode, KnowledgeCode, SkillCode, TestComplexComponent
from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import AuthoredValue, Converters, ConvertersType
from utils.semantics import (
    SemanticMap,
    _bytes_to_ints,
    _expected_bytes,
    collect_module_classes,
    flatten_iter,
    generate_signature_algorithmic,
    generate_signature_oop,
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
        elif isinstance(obj, (list, tuple)):
            return [convert(item) for item in obj]
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

def _split_flattened_aliases(flattened_aliases: str) -> tuple[str, ...]:
    return tuple(alias.strip().capitalize() for alias in flattened_aliases.split(",") if alias.strip())

def _compute_nested_component_signatures_from_root_component_signature(
    root_component_signature: bytes,
    root_semantic_signature: tuple[int, ...],
    instance_semantic_map: SemanticMap,
) -> list[bytes] | None:
    """Given a root component signature and its semantic map, compute the signatures of any nested components."""
    semantic_elements = instance_semantic_map.elements
    nested_signatures: dict[type, bytes] = {}

    flattened_component_signature = flatten_iter(_bytes_to_ints(root_component_signature))
    print(f"{Fore.GREEN}{Style.DIM}Root component signature: ({len(flattened_component_signature)})\n                          {Style.RESET_ALL}{Fore.GREEN}{Style.BRIGHT}{flattened_component_signature}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.DIM}Root semantic signature:\n                          {Style.RESET_ALL}{Fore.MAGENTA}{Style.BRIGHT}{root_semantic_signature}{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}{Style.DIM}Root Domain:{Style.RESET_ALL}{Style.NORMAL}")
    domain_map = []
    for element in semantic_elements:
        from components.base import Primitive
        subclass_dict = Primitive.subclass_dict
        depth, domain_id, count = element
        class_from_domain_id = next((cls for cls, id in subclass_dict.items() if id == domain_id), None)
        domain_map.append((depth, domain_id, class_from_domain_id, count))
        print(f"    {Fore.YELLOW}{Style.DIM}{depth} - id: {Style.NORMAL}{domain_id}{Style.DIM}, #: {Style.NORMAL}{count}{Style.DIM}{Fore.GREEN} - [{class_from_domain_id.__name__ if class_from_domain_id else 'Unknown'}]{Style.DIM}{Style.RESET_ALL}")
    
    print(f"\n{Fore.LIGHTCYAN_EX}{Style.NORMAL}Nested Domains:{Style.RESET_ALL}{Style.NORMAL}")
    for depth, domain_id, class_from_domain_id, count in domain_map:
        if depth > 0:
            print(f"    {Fore.LIGHTCYAN_EX}{Style.DIM}{depth} - id: {Style.NORMAL}{domain_id}{Style.DIM}, #: {Style.NORMAL}{count}{Style.DIM}{Fore.GREEN} - [{class_from_domain_id.__name__ if class_from_domain_id else 'Unknown'}]{Style.DIM}{Style.RESET_ALL}")
            nested_signatures[class_from_domain_id] = bytes(1) # Placeholder

    print()
    final_result = []
    first_domain = domain_map[0]
    first_domain_id = first_domain[1]
    first_domain_count = first_domain[3]
    final_result.append(first_domain_id)
    final_result.extend(flatten_iter(flattened_component_signature[1:first_domain_count+1]))
    seen = set()
    seen.add((0, first_domain_id))

    iterator = it.count(start = first_domain_count, step = 1)
    i_slice = it.islice(iterator, len(flattened_component_signature))
    print(f"{Style.DIM}iSlice: {list(i_slice)}{Style.RESET_ALL}")
    
    step_result = []
    print(f"{Style.DIM}First Result = {Style.NORMAL}{Style.RESET_ALL}{Style.NORMAL}{final_result}\n")
    for depth, domain_id, class_from_domain_id, count in domain_map[1:]: # Skip the first domain since we've already processed it
        step_result.clear()
        step = next(iterator)
        added_to_seen = False
        print(f"{Style.DIM}iSlice: {iter(i_slice)}{Style.RESET_ALL}")
        print(f"{Style.DIM}Step      = {step}{Style.RESET_ALL}")
        print(f"{Style.DIM}Count     = {Style.RESET_ALL}{Style.NORMAL}{count}{Style.RESET_ALL}")
        print(f"{Style.DIM}id        = {Style.RESET_ALL}{Style.NORMAL}{domain_id}{Style.RESET_ALL}             {Style.DIM}{Fore.GREEN}[{class_from_domain_id.__name__ if class_from_domain_id else 'Unknown'}]{Style.RESET_ALL}")
        if (depth, domain_id) not in seen:
            step_result.append(domain_id)
            seen.add((depth, domain_id))
            added_to_seen = True
            step_result.extend(flatten_iter(flattened_component_signature[step:step+count]))
        else:
            step_result.extend(flatten_iter(flattened_component_signature[step:step+count]))
        print(f"{Style.DIM}+Seen = {Style.RESET_ALL}{Style.NORMAL}{added_to_seen}{Style.RESET_ALL}")
        print(f"            {Style.DIM}Step Result = {Style.NORMAL}{Style.RESET_ALL}{Style.NORMAL}{step_result}")
        
        final_result.extend(step_result)

    print(f"             {Style.DIM}Root = {Style.RESET_ALL}{Style.DIM}{flattened_component_signature}{Style.RESET_ALL}")    
    print(f"            {Style.DIM}Value = {Style.NORMAL}{Style.RESET_ALL}{Fore.GREEN}{Style.BRIGHT}{final_result}")

    print(f"\n{Style.DIM}Current Nested Signatures:{Style.RESET_ALL}")
    for cls, sig in nested_signatures.items():
        print(f"    {Fore.BLUE}{Style.BRIGHT}{sig}: {Fore.GREEN}{Style.DIM}[{cls.__name__}]{Style.RESET_ALL}")


    pass

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      SEMANTIC SEARCH ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

def get_semantics_from_instance(instance: Any, definitions: DefinitionsIndices) -> None:
    """Helper function to get the semantics of a component instance using the by_signature index."""
    print(f"{Style.DIM}Semantics for '{instance}'...{Style.NORMAL}")
    flattened_semantic_signature = flatten_iter(instance.semantic_signature)
    component_signature = instance.component_signature
    # print(f"{Fore.MAGENTA}Component signature: bytes = {component_signature}{Style.RESET_ALL}")
    # print(f"{Fore.MAGENTA}Component signature: ints = {_bytes_to_ints(component_signature)}{Style.RESET_ALL}")
    # print(f"{Fore.MAGENTA}Semantic Signature: list[int] = {flattened_semantic_signature}{Style.RESET_ALL}")
    instance_name_flattened_aliases = definitions.by_signature.get(instance.component_signature)
    instance_name = _split_flattened_aliases(instance_name_flattened_aliases) if instance_name_flattened_aliases else ("Unknown",)
    # print(f"{Fore.GREEN}{instance.__class__.__name__}: {instance_name[0]} ({', '.join(instance_name[1:])}){Style.RESET_ALL}")
    print()
    
    semantic_map = instance.semantic_map
    semantic_elements = semantic_map.elements
        
    nested_domains = []
    for depth, domain_id, count in semantic_elements:
        nested_domain_class = next((cls for cls, id in instance.subclass_dict.items() if id == domain_id), None)
        nested_domains.append((domain_id, count, nested_domain_class)) # if depth > 0 else None
    
    # print(f"\n{Fore.YELLOW}{Style.DIM}Nested domains:{Style.RESET_ALL}{Style.NORMAL}")
    # for domain_id, count, nested_domain_class in nested_domains:
    #     print(f"    {Fore.YELLOW}Domain ID: {domain_id}, Count: {count}, Class: {nested_domain_class.__name__ if nested_domain_class else 'Unknown'}{Style.RESET_ALL}{Style.NORMAL}")
    
    nested_signatures: list[int] = []
    nested_semantic_maps: list[SemanticMap] = []
    # for nested_domain in nested_domains:
    #     nested_domain_class = nested_domain[2]
    #     print(f"    {Fore.YELLOW}{Style.DIM}Domain = {Style.NORMAL}{nested_domain[0]}{Style.DIM} ({nested_domain_class.__name__}){Style.RESET_ALL}{Style.NORMAL}")
    #     nested_signatures.append(nested_domain[0])
        
    #     nested_semantic_map = nested_domain_class.semantic_map
    #     nested_semantic_maps.append(nested_semantic_map)

    #     nested_semantic_members = nested_semantic_map.members
    #     nested_semantic_elements = nested_semantic_map.elements
        
    #     display_semantic_elements(nested_semantic_elements, colour=Fore.YELLOW, style=Style.DIM, padding=4)
    #     display_semantic_members(nested_semantic_members, colour=Fore.CYAN, style=Style.NORMAL, padding=4)
    #     print()
    
    _ = _compute_nested_component_signatures_from_root_component_signature(
        root_component_signature=component_signature,
        root_semantic_signature=instance.semantic_signature,
        instance_semantic_map=semantic_map,
    )

if __name__ == "__main__":

    classes = collect_module_classes(module_name="components.data", base_classes=(Primitive,))
    definitions: DefinitionsIndices = build_definitions_indices(classes=classes)
    header("DEFINITIONS INDICES")
    # display_definitions_indices(definitions, index_name="by_signature", filter_by_type=KnowledgeCode)
    # display_definitions_indices(definitions, index_name="by_signature")
    # display_definitions_indices(definitions, index_name="by_member_identity")
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
        get_semantics_from_instance(component, definitions)
        print("\n" + "-"*80 + "\n")
