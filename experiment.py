from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, NamedTuple, get_type_hints

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

from components.base import Primitive, _filter_type_hints
from components.data import CharacteristicCode, KnowledgeCode, SkillCode
from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import DEFAULT_INT, AuthoredValue, Converters, ConvertersType
from utils.semantics import (
    _bytes_to_ints,
    collect_module_classes,
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
# ┃                                                                             HELPERS ┃
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
# endregion

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      SEMANTIC SEARCH ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

@dataclass
class SemanticMembersResult:
    member_name: str
    member_code: int
    aliases: tuple[str, ...]
@dataclass
class SemanticNestedClassResult:
    cls: type
    semantic_signature: tuple[int, ...]
    aliases: tuple[str, ...]
    members: list[SemanticMembersResult]
@dataclass
class SemanticSearchResult:
    instance: Any
    nested_classes: list[SemanticNestedClassResult]

def get_semantics_from_instance(instance: Any, definitions: DefinitionsIndices) -> None:
    """Helper function to get the semantics of a component instance using the by_signature index."""
    print(f"{Fore.GREEN}Getting semantics for instance of type '{instance.__class__.__name__}'...{Style.RESET_ALL}")
    semantic_map = instance.semantic_map
    for (key, type), member_identity in semantic_map.members.items():
        print(f"{member_identity}: {key} {type}")
    print()
    for element in semantic_map.elements:
        print(f"Depth: {element.depth}, Domain Identity: {element.domain_identity}, Pre-nested Count: {element.pre_nested_count}")
    
    index_header = definitions.by_header.get(instance.__class__, [])
    print(f"\n{Fore.YELLOW}Index header for instance's class: {index_header}{Style.RESET_ALL}")

    available_members = {}
    for sheet in index_header:
        # If sheet appears in semantic_map.members key then add it to available members with the member identity as the value
        for (name, type), member_identity in semantic_map.members.items():
            if name == sheet:
                available_members[name] = member_identity
                break
    print(f"\n{Fore.CYAN}Available members: {available_members}{Style.RESET_ALL}")
    
    

if __name__ == "__main__":

    classes = collect_module_classes(module_name="components.data", base_classes=(Primitive,))
    definitions: DefinitionsIndices = build_definitions_indices(classes=classes)
    header("DEFINITIONS INDICES")
    # display_definitions_indices(definitions, index_name="by_signature", filter_by_type=KnowledgeCode)
    # display_definitions_indices(definitions, index_name="by_signature")
    # display_definitions_indices(definitions, index_name="by_member_identity")
    display_definitions_indices(definitions, index_name="by_header")
    # display_definitions_indices(definitions)

    initialised_components = [
        initialised_skill_code := SkillCode(key=12, set=1, group=-99),
        initialised_knowledge_code := KnowledgeCode(key=6, focus=-99, associated_skill=initialised_skill_code),
        initialised_charcteristic_code := CharacteristicCode(upp_position=1, subtype=0, category=1)
    ]
    header("SEMANTICS")
    print("\n")
    for component in initialised_components:
        get_semantics_from_instance(component, definitions)
        print("\n" + "-"*80 + "\n")
