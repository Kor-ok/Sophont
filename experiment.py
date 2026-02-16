from __future__ import annotations

import json
import logging
import re
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module
from types import MappingProxyType
from typing import Any, NamedTuple, Optional, get_type_hints

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

from humaniseT5.semantics import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import (
    convert_comma_delimited_str_to_tuple,
    lowercase_and_strip,  # Will be used in the next iteration - Please do not remove
)
from semantics.base import Primitive
from semantics.data import CharacteristicCode, KnowledgeCode, SkillCode
from utils.terminal import divider, header

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
Signature: TypeAlias = tuple[int, ...]

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

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                    COMPONENT HELPERS ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
def return_recursive_types(
    cls: type,
    seen: Optional[set[type]] = None
) -> OrderedDict[type, tuple[DomainIdentity, MembersLength]]:
    """Return a dictionary of all types that are recursively referenced by the given class,
    including self where the key is the class and the value is a tuple of the class's domain identity and members length.
    Member lengths are + 1 to account for the domain identity at the start of the signature for each class EXCEPT
    the initial class to allow for self recursion without including the domain identity in the member count for that 
    initial class."""
    if seen is None:
        seen = set()
    if cls in seen:
        return OrderedDict({cls: (cls.subclass_dict[cls], len(cls.member_dict))}) # Return the recursive type with its domain identity and members length
    seen.add(cls)
    recursive_types = OrderedDict()
    is_recursive = False
    for _, field_type in cls.member_dict.values():
        for class_type, domain_identity in cls.subclass_dict.items():
            if field_type == class_type:
                is_recursive = True

    primary_domain_identity = cls.subclass_dict[cls]
    if is_recursive:
        for _, field_type in cls.member_dict.values():
            for class_type, domain_identity in cls.subclass_dict.items():
                if field_type == class_type:
                    members_length = len(class_type.member_dict) + 1
                    recursive_types[class_type] = (domain_identity, members_length)
                    # Now deal with the self class where if it is recursive, we want to include it in the result with its domain identity and members length, but we don't want to add +1 to the members length for the initial class to allow for self recursion without including the domain identity in the member count for that initial class
                    self_members_length = len(cls.member_dict)
                    recursive_types[cls] = (primary_domain_identity, self_members_length) # Keep the existing members length for the initial class to allow for self recursion without including the domain identity in the member count for that initial class
                    recursive_types.move_to_end(cls, last=False)
    else:
        # We only add itself to the recursive types
        recursive_types[cls] = (primary_domain_identity, len(cls.member_dict) + 1) # Add +1 to account for the domain identity at the start of the signature for each class
    
    if not recursive_types:
        raise ValueError(f"No recursive types found for class {cls.__name__}.")
    return recursive_types

def construct_composite_signature(parse_signature: Signature, recursive_types: dict[type, tuple[DomainIdentity, MembersLength]]) -> Signature:
    """Construct a composite signature by adding the domain identity at the start of the parse signature tuple, to create a unique key for the by_signature index."""
    composite_signature: Signature = ()
    target_signature_length = sum(members_length for _, members_length in recursive_types.values())
    cummulative_members_length = 0
    for cls, (domain_identity, members_length) in recursive_types.items():
        parse_signature_portion = parse_signature[:members_length - 1]
        composite_signature += (domain_identity,) + parse_signature_portion
        if len(composite_signature) >= target_signature_length:
            break  # Stop once we've reached the target signature length to avoid adding extra domain identities and member values beyond what is needed for the composite signature
        cummulative_members_length += members_length
        parse_signature = parse_signature[members_length - 1:]
    
    return composite_signature

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      COLLECT CLASSES ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
def collect_module_classes(
    module_name: str,
    base_classes: tuple[type, ...],
) -> Any:

    module = import_module(module_name)

    results = []
    for _, obj in vars(module).items():
        # get everything from __module__ = components.data and who's base class is in base_classes
        if getattr(obj, "__module__", None) == module_name\
            and any(issubclass(obj, base) for base in base_classes):
            results.append(obj)
    
    return results

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                        BUILD INDICES ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
def build_definitions_indices(
    classes: list[type],
    language: str = "en",
) -> Any:
    
    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                                         IO ONCE ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    data: dict[str, pd.DataFrame] = pd.read_excel(
        DEFINITIONS_XLSX_PATH, sheet_name=None, engine="openpyxl"
    )

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                  SANITISE AUTHORED WITH RUNTIME ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    # The sheet names in the Excel File are in the format "ComponentName" i.e. 
    # "CharacteristicCode" or "SkillCode",
    # and "ComponentName.member_name" i.e. 
    # "CharacteristicCode.upp_position" or "SkillCode.key"
    base_map: dict[type, list[str]] = {}
    for component_cls in classes:
        # We use the component class name as the key in the base map, 
        # and the value is a list of the Excel sheet names that start with that component
        # class name, i.e. all the sheets relevant to that component class, including the
        # sheet for the signature and the sheets for each member.
        base_map.setdefault(component_cls, [])
        for sheet_name in data:
            if sheet_name.startswith(component_cls.__name__ + "."): # Looking only for the "." prefixed sheets
                member_name = sheet_name
                base_map[component_cls].append(member_name)
    # print(f"Base map: {Fore.CYAN}{json.dumps(base_map, indent=4)}")

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                                           BUILD ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    
    by_signature: BySignature = {}
    by_member_identity: ByMemberIdentity = {}
    by_alias_for_signature: ByAliasForSignature = {}
    by_alias_for_member_identity: ByAliasForMemberIdentity = {}

    
    for component_cls, sheets in base_map.items():
        # print(f"Processing component: {Fore.YELLOW}{component_cls.__name__}...")
        # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        # ┃                                                        TYPE RECURSION CHECK ┃
        # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        recursive_types = return_recursive_types(component_cls)
        # print(f" - Types for {Fore.GREEN}'{component_cls.__name__}': {Fore.YELLOW}{recursive_types}")

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
            for header in check_for_headers:
                if header not in data[sheet].columns:
                    raise ValueError(f"Expected column '{header}' not found in sheet '{sheet}'")

            df_sheet = data[sheet]
            for _, row in df_sheet.iterrows():
                if row.get("lang") != language:
                    continue
                
                flattened_aliases: str = ""
                
                signature: tuple[int, ...] = convert_comma_delimited_str_to_tuple(row.get(value_col), type=int)
                canonical = row.get("canonical") 
                flattened_aliases += f"{canonical}, "
                aliases = convert_comma_delimited_str_to_tuple(row.get("aliases"), type=str)
                # We put canonical as the first value in the flattened alias map, so that 
                # we can easily extract it in the reverse lookup without needing to check the alias map separately
                flattened_aliases += ", ".join(aliases)
                # print(f"        {Style.DIM}Aliases for signature key {Style.NORMAL}{signature}: {flattened_aliases}")

                # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                # ┃                                                        APPLY TO INDICES ┃
                # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                
                primary_identity, _ = recursive_types.get(component_cls, (None, None))
                # print(f"Primary identity for component '{component_cls.__name__}': {primary_identity}")
                if primary_identity is None:
                    raise ValueError(f"Primary identity for component class '{component_cls.__name__}' not found in recursive types.")
                
                if suffix == "signature":
                    # print(f"Processing signature sheet for component '{component_cls.__name__}' with signature {signature} and aliases {flattened_aliases}...")
                    # Forward index: (DomainIdentity,Signature) → FlattenedAliasMap
                    # Create a composite signature by adding the domain identity at the start of the signature tuple, to create a unique key for the by_signature index.
                    composite_signature = construct_composite_signature(signature, recursive_types)
                    # if composite_signature[0] == 2:
                    #     print(f"Composite Signature: {composite_signature}")
                    by_signature[composite_signature] = flattened_aliases

                    # Reverse index: (DomainIdentity, FlattenedAliasMap) → Signature
                    by_alias_for_signature[(primary_identity, flattened_aliases)] = signature
                else:
                    # Member index: (DomainIdentity, MemberIdentity) → FlattenedAliasMap
                    member_name = suffix
                    member_identity = next((index for cls in classes if component_cls in cls.subclass_dict for index, (name, type) in cls.member_dict.items() if name == member_name), None)
                    if member_identity is None:
                        raise ValueError(f"Member identity for member '{member_name}' of component '{component_cls.__name__}' not found in any of the provided classes.")
                    
                    code: int = signature[0]  # Unwrap the single value from the tuple for the member index since it's not a signature for the whole component, but just a value for a specific member
                    by_member_identity[(primary_identity, member_identity, code)] = flattened_aliases

                    # Reverse member index: (DomainIdentity, MemberIdentity, FlattenedAliasMap) → Signature
                    by_alias_for_member_identity[(primary_identity, member_identity, flattened_aliases)] = code
                
    return DefinitionsIndices(
        by_header= MappingProxyType(base_map),
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
            print(f"{Fore.GREEN}{signature} → {aliases}{Style.RESET_ALL}")
            # With a counter for the number of entries in the index

        print(f"\n{Fore.CYAN}Reverse index (by_alias_for_signature):{Style.RESET_ALL}")
        for (domain_identity, flattened_aliases), signature in definitions.by_alias_for_signature.items():
            print(f"{Fore.CYAN}(Domain ID: {domain_identity}, Aliases: {flattened_aliases}) → {signature}{Style.RESET_ALL}")
        
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
    member_value: int
    aliases: tuple[str, ...]
@dataclass
class SemanticNestedClassResult:
    cls: type
    signature: tuple[int, ...]
    aliases: tuple[str, ...]
    members: list[SemanticMembersResult]
@dataclass
class SemanticSearchResult:
    instance: Any
    nested_classes: list[SemanticNestedClassResult]

def get_semantics_from_instance(instance: Any, definitions: DefinitionsIndices) -> None:
    """Helper function to get the semantics of a component instance using the by_signature index."""
    
    def _parse_signature_portion_from_type(cls: type, primary_signature: Signature) -> tuple[int, ...]:
        """Helper function to parse a portion of the signature tuple that corresponds to a specific class, using the member_dict of that class to map the values in the signature portion to their corresponding member names."""
        parsed_result = ()
        member_dict = cls.member_dict
        is_recursive = False
        for _, field_type in member_dict.values():
            for class_type, domain_identity in cls.subclass_dict.items():
                if field_type == class_type:
                    is_recursive = True
                    break
        
        if is_recursive:
            members_length = len(member_dict) - 1
        else:
            members_length = len(member_dict)
        
        logger.debug(f"Length of members for class '{cls.__name__}': {members_length}")
        for index, (member_name, member_type) in member_dict.items():
            member_value = primary_signature[index + 1:members_length + 1]
            logger.debug(f"Extracted member value: {member_value}")
            parsed_result += member_value
            if len(member_value) > members_length -1:
                break  # Stop once we've parsed the expected number of member values for this class to avoid adding extra values beyond what is needed for the signature portion corresponding to this class

        logger.debug(f"Parsed signature portion for class '{cls.__name__}': {parsed_result}")
        return parsed_result
    
    def _get_available_members_from_type(cls: type) -> list[tuple[int, str]]:
        """Helper function to get the available member sheets for a specific class from the by_header index."""
        available_members: list[str] = definitions.by_header.get(cls, [])
        for member in available_members:
            if member == cls.__name__ + ".signature":
                available_members.remove(cls.__name__ + ".signature") # We remove the signature sheet from the available members since we have already used it to get the semantics for the instance, and we want to focus on the member sheets for the next steps of looking up the semantics for each member separately.
        available_member_identities: list[tuple[int, str]] = []
        for member in available_members:
            member_name = member.split(".", 1)[1]
            member_identity = next((index for cls in classes if instance.__class__ in cls.subclass_dict for index, (name, type) in cls.member_dict.items() if name == member_name), None)
            if member_identity is None:
                raise ValueError(f"Member identity for member '{member_name}' of component '{instance.__class__.__name__}' not found in any of the provided classes.")
            available_member_identities.append((member_identity, member_name))

        return available_member_identities
    
    def _display_semantic_search_result(result: SemanticSearchResult) -> None:
        """Helper function to display the semantic search result in a readable format."""
        info = str(result.instance)

        for nested_class in result.nested_classes:
            
            canonical_alias = (nested_class.aliases.split(",")[0]) if nested_class.aliases else "N/A"
            key_regex = re.compile(r"key=\d+" r"|upp_position=\d+, subtype=\d+" r"|value=\d+")
            match = key_regex.search(info)
            if match:
                info = info.replace(match.group(0), f"{canonical_alias.capitalize()}")
            for member in nested_class.members:
                replace = ""
                replace += f"{member.member_name}={member.member_value}"
                canonical_alias = (member.aliases.split(",")[0]) if member.aliases else "N/A"
                info = info.replace(replace, canonical_alias.capitalize())
                
        info = info.replace("-99", "Undefined")
        print(info)

    debug_result = {}

    instance_object = instance
    debug_result.update({instance_object: {}})
    
    semantic_search_result = SemanticSearchResult(
        instance=instance,
        nested_classes=[]
    )

    signature = instance.signature
    debug_result[instance_object].update({"signature": str(signature)})

    instance_subclass_dict = instance.subclass_dict

    instance_type = instance.__class__
    debug_result[instance_object].update({instance_type.__name__: {}})

    instance_domain_identity = instance_subclass_dict.get(instance_type)
    if instance_domain_identity is None:
        raise ValueError(f"Domain identity for instance type '{instance_type.__name__}' not found in its subclass dict.")

    primary_signature_portion = _parse_signature_portion_from_type(instance_type, signature)
    debug_result[instance_object][instance_type.__name__].update({"signature": str(primary_signature_portion)})

    search_result_by_signature = definitions.by_signature.get(signature)
    debug_result[instance_object][instance_type.__name__].update({"aliases": search_result_by_signature})

    semantic_nested_class = SemanticNestedClassResult(
        cls=instance_type,
        signature=primary_signature_portion,
        aliases=search_result_by_signature if search_result_by_signature is not None else (),
        members=[]
    )
    semantic_search_result.nested_classes.append(semantic_nested_class)

    available_members = _get_available_members_from_type(instance_type)
    recursive_types = return_recursive_types(instance_type)
    if available_members:
        for member_identity, member_name in available_members:
            if len(recursive_types) > 1:
                member_identity += 1
            if primary_signature_portion[member_identity] == -99:
                aliases_for_member = "UNDEFINED"
            else:
                aliases_for_member = definitions.by_member_identity.get((instance_domain_identity, member_identity, primary_signature_portion[member_identity]))
            # print(f"Aliases for member '{member_name}' in domain identity {instance_domain_identity} and signature portion {primary_signature_portion[member_identity + 1]}: {aliases_for_member}")
            debug_result[instance_object][instance_type.__name__].update({member_name: {"value": primary_signature_portion[member_identity], "aliases": aliases_for_member}})

            semantic_members_result = SemanticMembersResult(
                member_name=member_name,
                member_value=primary_signature_portion[member_identity],
                aliases=aliases_for_member if aliases_for_member is not None else ()
            )
            semantic_search_result.nested_classes[-1].members.append(semantic_members_result)

    if len(recursive_types) > 1:

        signature_portion = signature[recursive_types[instance_type][1]:] # We take the portion of the signature that corresponds to the recursive type, which is the initial class in the recursive types ordered dict, and we use the members length from the recursive types to know how many values to extract from the signature for this portion.
        portion_type: type
        for type_class, domain_identity in instance_subclass_dict.items():
            if domain_identity == signature_portion[0]:
                portion_type = type_class
                break
        if portion_type is None:
            raise ValueError(f"Portion type for signature portion {signature_portion} not found in instance subclass dict.")
        debug_result[instance_object][instance_type.__name__].update({portion_type.__name__: {}})
        nested_signature_portion = _parse_signature_portion_from_type(portion_type, signature_portion)
        debug_result[instance_object][instance_type.__name__][portion_type.__name__].update({"signature": str(nested_signature_portion)})
        
        search_result_by_signature_portion = definitions.by_signature.get(signature_portion)
        debug_result[instance_object][instance_type.__name__][portion_type.__name__].update({"aliases": search_result_by_signature_portion})

        semantic_nested_class = SemanticNestedClassResult(
            cls=portion_type,
            signature=nested_signature_portion,
            aliases=search_result_by_signature_portion if search_result_by_signature_portion is not None else (),
            members=[]
        )
        semantic_search_result.nested_classes.append(semantic_nested_class)

        available_members = _get_available_members_from_type(portion_type)
        # print(f"Available members for {portion_type.__name__}: {available_members}")

        if available_members:
            for member_identity, member_name in available_members:
                if signature_portion[member_identity + 1] == -99:
                    aliases_for_member = "UNDEFINED"
                else:
                    aliases_for_member = definitions.by_member_identity.get((domain_identity, member_identity, signature_portion[member_identity + 1]))
                # print(f"Aliases for member '{member_name}' in domain identity {domain_identity} and signature portion {signature_portion[member_identity + 1]}: {aliases_for_member}")
                debug_result[instance_object][instance_type.__name__][portion_type.__name__].update({member_name: {"value": signature_portion[member_identity + 1], "aliases": aliases_for_member}})

                semantic_members_result = SemanticMembersResult(
                    member_name=member_name,
                    member_value=signature_portion[member_identity + 1],
                    aliases=aliases_for_member if aliases_for_member is not None else ()
                )
                semantic_search_result.nested_classes[-1].members.append(semantic_members_result)

    _display_semantic_search_result(semantic_search_result)    
    #display_component_info(debug_result)
    

if __name__ == "__main__":

    classes = collect_module_classes(module_name="semantics.data", base_classes=(Primitive,))
    definitions: DefinitionsIndices = build_definitions_indices(classes=classes)
    # header("DEFINITIONS INDICES")
    # display_definitions_indices(definitions, index_name="by_signature", filter_by_type=KnowledgeCode)
    # display_definitions_indices(definitions, index_name="by_signature")
    # display_definitions_indices(definitions, index_name="by_member_identity")

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
