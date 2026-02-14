from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Mapping
from importlib import import_module
from typing import Any, NamedTuple

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

from components.base import Primitive
from components.data import KnowledgeCode, SkillCode
from humaniseT5.definitions import DEFINITIONS_XLSX_PATH
from humaniseT5.utils import (
    convert_comma_delimited_str_to_tuple,
    lowercase_and_strip,
)

#region SETUP
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                                SETUP ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
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
Signature: TypeAlias = tuple[int, ...]

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]
FlattenedAliasMap: TypeAlias = str

SearchHeader: TypeAlias = dict[str, list[str]]

BySignature: TypeAlias = Mapping[Signature, FlattenedAliasMap] # Creating a single Signature tuple by adding the domain identity at the start.
"""Forward index: (DomainIdentity, Signature) → FlattenedAliasMap."""

ByAliasForSignature: TypeAlias = Mapping[tuple[DomainIdentity, FlattenedAliasMap], Signature]
"""Reverse index: (DomainIdentity, FlattenedAliasMap) → Signature."""

ByMemberIdentity: TypeAlias = Mapping[tuple[DomainIdentity, MemberIdentity, Signature], FlattenedAliasMap]
"""Member index: (DomainIdentity, MemberIdentity, Signature) → FlattenedAliasMap."""

ByAliasForMemberIdentity: TypeAlias = Mapping[tuple[DomainIdentity, MemberIdentity, FlattenedAliasMap], Signature]
"""Reverse member index: (DomainIdentity, MemberIdentity, FlattenedAliasMap) → Signature."""
#endregion

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
    base_map: dict[str, list[str]] = {}
    for component_cls in classes:
        # We use the component class name as the key in the base map, 
        # and the value is a list of the Excel sheet names that start with that component
        # class name, i.e. all the sheets relevant to that component class, including the
        # sheet for the signature and the sheets for each member.
        base_map.setdefault(component_cls.__name__, [])
        for sheet_name in data:
            if sheet_name.startswith(component_cls.__name__ + "."): # Looking only for the "." prefixed sheets
                member_name = sheet_name
                base_map[component_cls.__name__].append(member_name)
    # print(f"Base map: {Fore.CYAN}{json.dumps(base_map, indent=4)}")

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃                                                                           BUILD ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    # Indices built in one pass ---------------------------------------------
    
    by_signature: BySignature = {}
    by_member_identity: ByMemberIdentity = {}
    by_alias_for_signature: ByAliasForSignature = {}
    by_alias_for_member_identity: ByAliasForMemberIdentity = {}

    
    for component_name, sheets in base_map.items():
        # print(f"Processing component: {Fore.GREEN}{component_name}...")
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
                domain_identity: int | None = next((cls.subclass_dict[component_name] for cls in classes if component_name in cls.subclass_dict), None)
                if domain_identity is None:
                        raise ValueError(f"Domain identity for component '{component_name}' not found in any of the provided classes.")
                # print(f"Domain identity for component '{component_name}': {domain_identity}")
                if suffix == "signature":
                    # print(f"Processing signature sheet for component '{component_name}' with signature {signature} and aliases {flattened_aliases}...")
                    # Forward index: (DomainIdentity,Signature) → FlattenedAliasMap
                    # Create a composite signature by adding the domain identity at the start of the signature tuple, to create a unique key for the by_signature index.
                    composite_signature: Signature = (domain_identity,) + signature
                    by_signature[composite_signature] = flattened_aliases

                    # Reverse index: (DomainIdentity, FlattenedAliasMap) → Signature
                    by_alias_for_signature[(domain_identity, flattened_aliases)] = signature
                else:
                    # Member index: (DomainIdentity, MemberIdentity) → FlattenedAliasMap
                    member_name = suffix
                    member_identity = next((index for cls in classes if component_name in cls.subclass_dict for index, name in cls.member_dict.items() if name == member_name), None)
                    if member_identity is None:
                        raise ValueError(f"Member identity for member '{member_name}' of component '{component_name}' not found in any of the provided classes.")
                    by_member_identity[(domain_identity, member_identity, signature)] = flattened_aliases

                    # Reverse member index: (DomainIdentity, MemberIdentity, FlattenedAliasMap) → Signature
                    by_alias_for_member_identity[(domain_identity, member_identity, flattened_aliases)] = signature
                
    return DefinitionsIndices(
        by_header=base_map,
        by_signature=by_signature, 
        by_alias_for_signature=by_alias_for_signature, 
        by_member_identity=by_member_identity, 
        by_alias_for_member_identity=by_alias_for_member_identity
        )

class DefinitionsIndices(NamedTuple):
    """Immutable container holding multiple lookup indices built from the
    Definitions workbook.  Lookup helpers accept this as a single
    ``search_index`` argument and internally select the correct
    sub-index."""
    by_header: SearchHeader
    by_signature: BySignature
    by_alias_for_signature: ByAliasForSignature
    by_member_identity: ByMemberIdentity
    by_alias_for_member_identity: ByAliasForMemberIdentity

def display_definitions_indices(definitions: DefinitionsIndices, index_name: str | None = None) -> None:
    print("Displaying definitions indices:\n")

    if index_name:
        index = getattr(definitions, index_name, None)
        if index is not None:
            print(f"{Fore.GREEN}Index: {index_name}{Style.RESET_ALL}")
            for key, value in index.items():
                print(f"{Fore.GREEN}{key} → {value}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Index '{index_name}' not found in definitions.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Forward index (by_signature):{Style.RESET_ALL}")
        for signature, aliases in definitions.by_signature.items():
            print(f"{Fore.GREEN}{signature} → {aliases}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}Reverse index (by_alias_for_signature):{Style.RESET_ALL}")
        for (domain_identity, flattened_aliases), signature in definitions.by_alias_for_signature.items():
            print(f"{Fore.CYAN}(Domain ID: {domain_identity}, Aliases: {flattened_aliases}) → {signature}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}Member index (by_member_identity):{Style.RESET_ALL}")
        for (domain_identity, member_identity, signature), aliases in definitions.by_member_identity.items():
            print(f"{Fore.BLUE}(Domain ID: {domain_identity}, Member ID: {member_identity}, Signature: {signature}) → {aliases}{Style.RESET_ALL}")

        print(f"\n{Fore.MAGENTA}Reverse member index (by_alias_for_member_identity):{Style.RESET_ALL}")
        for (domain_identity, member_identity, flattened_aliases), signature in definitions.by_alias_for_member_identity.items():
            print(f"{Fore.MAGENTA}(Domain ID: {domain_identity}, Member ID: {member_identity}, Aliases: {flattened_aliases}) → {signature}{Style.RESET_ALL}")

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                      SEMANTIC SEARCH ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
def get_subclass_object_by_index(base_cls: type, index: DomainIdentity) -> type:
    """Helper function to get the subclass object of a base class by its index in the subclass dict."""
    if hasattr(base_cls, "subclass_dict"):
        subclass_dict = base_cls.subclass_dict
        for subclass_name, subclass_index in subclass_dict.items():
            if subclass_index == index:
                for subclass in base_cls.__subclasses__():
                    if subclass.__name__ == subclass_name:
                        return subclass
    raise ValueError(f"Index {index} not found in {base_cls.__name__}'s subclass dict")

def get_semantics_from_instance(instance: Any, definitions: DefinitionsIndices) -> None:
    """Helper function to get the semantics of a component instance using the by_signature index."""
    print(f"Instance: {Fore.GREEN}{instance.__class__.__name__}")
    base_class = instance.__class__.mro()[-2] # Get the base class of the instance, which is the second to last in the MRO (the last one is 'object')
    print(f"Base Class: {Fore.GREEN}{base_class.__name__}")
    signature = instance.signature
    print(f"{Style.DIM}Instance Signature: {Style.RESET_ALL}{Style.BRIGHT}{signature}")


    print("\n")

    involved_classes_with_member_counts = {}

    pointer = 0
    while pointer < len(signature):
        domain_identity = signature[pointer]
        subclass = get_subclass_object_by_index(base_class, domain_identity)
        class_member_count = len(subclass.member_dict)
        class_member_count_with_domain_identity = class_member_count + 1 # +1 to account for the domain identity at the start of the signature for each class
        # print(f"Member Count for {subclass.__name__}: {class_member_count} (including domain identity: {class_member_count_with_domain_identity})")
        involved_classes_with_member_counts[subclass] = class_member_count_with_domain_identity
        pointer += class_member_count_with_domain_identity

    print(f"Involved Classes with member counts: {Fore.GREEN}{json.dumps({cls.__name__: count for cls, count in involved_classes_with_member_counts.items()}, indent=4)}")
    print("\n")

    # filtered_search_header = {}
    # for involved_class, member_count in involved_classes_with_member_counts.items():
    #     filtered_search_header.setdefault(involved_class.__name__, [])
    #     for sheet_name in definitions.by_header.get(involved_class.__name__, []):
    #         if sheet_name.startswith(involved_class.__name__ + "."): # Looking only for the "." prefixed sheets
    #             member_name = sheet_name
    #             filtered_search_header[involved_class.__name__].append(member_name)

    # print(f"Filtered search header based on involved classes: {Fore.CYAN}{json.dumps(filtered_search_header, indent=4)}")
    # print("\n")

    involved_classes_with_signatures = {}
    pointer = 0
    subset_index = 0
    subset_count = len(involved_classes_with_member_counts)
    # print(f"subset_count= {subset_count}")
    while pointer < len(signature) and subset_index < subset_count:
        # print(f"\nsubset_index % subset_count: {subset_index % subset_count}")
        current_length = list(involved_classes_with_member_counts.items())[subset_index % subset_count][1]
        # print(f"Current subset length: {current_length}")
        subset_index += 1
        # print(f"Subset index after increment: {subset_index}")
        slice_start = pointer
        slice_end = pointer + current_length
        sliced_values = signature[slice_start:slice_end]
        # print(f"Sliced values: {sliced_values} using slice indices [{slice_start}:{slice_end}]")
        involved_classes_with_signatures = {list(involved_classes_with_member_counts.keys())[i]: signature[sum(list(involved_classes_with_member_counts.values())[:i]):sum(list(involved_classes_with_member_counts.values())[:i+1])] for i in range(len(involved_classes_with_member_counts))}
        pointer += current_length
        if pointer + current_length > len(signature):
            break  # Avoid slicing beyond the end of the signature
        
    print(f"Involved classes with their extracted signatures: {Fore.BLUE}{involved_classes_with_signatures}")

    # Now use definitions.by_signature to get the semantics for each involved class based on their extracted signatures
    if subset_count > 1:
        composite_signatures = {}
        for involved_class, involved_signature in involved_classes_with_signatures.items():
            # Use the first element of the involved signature as the domain identity to look up the class name in the subclass dict, and then use the class name to look up the semantics in the by_signature index. We also need to convert the involved signature to a tuple of ints if it's not already, to match the format of the signatures in the by_signature index.
            domain_identity = involved_signature[0]
            # print(f"\nDomain identity: {Fore.YELLOW}{domain_identity}{Style.RESET_ALL}")
            signature_tuple = tuple(involved_signature[1:])
            # print(f"Signature: {Fore.YELLOW}{signature_tuple}{Style.RESET_ALL}")
            composite_signature = (domain_identity,) + signature_tuple
            composite_signatures[involved_class.__name__] = composite_signature

        print(f"Composite signature: {Fore.YELLOW}{composite_signatures}{Style.RESET_ALL}")
        # Get the Mapping
        # For the first one combine the two composite_signatures into a single composite signature by concatenating the tuples,
        #  ommitting the first value of the second composite signature since it's the same domain identity, and then look up the semantics for that combined signature in the by_signature index.
        first_combined_composite_signature = tuple(composite_signatures.values())[0] + tuple(composite_signatures.values())[1][1:]
        print(f"Combined composite signature: {Fore.YELLOW}{first_combined_composite_signature}{Style.RESET_ALL}")
        
        try:
            semantics: FlattenedAliasMap = definitions.by_signature[first_combined_composite_signature]
        except KeyError:
            semantics = "Semantics not found for this signature"
        print(f"Semantics for class {involved_class.__name__} with signature {first_combined_composite_signature}: {Fore.GREEN}{semantics}{Style.RESET_ALL}")
        # For the second one, we just use the second composite signature
        second_composite_signature = composite_signatures[list(composite_signatures.keys())[1]]
        print(f"Second composite signature: {Fore.YELLOW}{second_composite_signature}{Style.RESET_ALL}")
        try:
            semantics: FlattenedAliasMap = definitions.by_signature[second_composite_signature]
        except KeyError:
            semantics = "Semantics not found for this signature"
        print(f"Semantics for class {involved_class.__name__} with signature {second_composite_signature}: {Fore.GREEN}{semantics}{Style.RESET_ALL}")
    else:
        involved_classes_with_signatures = {list(involved_classes_with_member_counts.keys())[0]: signature}
        involved_class = list(involved_classes_with_signatures.keys())[0]
        single_composite_signature = tuple(signature)
        print(f"Single composite signature: {Fore.YELLOW}{single_composite_signature}{Style.RESET_ALL}")
        try:
            semantics: FlattenedAliasMap = definitions.by_signature[single_composite_signature]
        except KeyError:
            semantics = "Semantics not found for this signature"
        print(f"Semantics for class {involved_class.__name__} with signature {single_composite_signature}: {Fore.GREEN}{semantics}{Style.RESET_ALL}")

if __name__ == "__main__":

    classes = collect_module_classes(module_name="components.data", base_classes=(Primitive,))
    definitions: DefinitionsIndices = build_definitions_indices(classes=classes)
    # display_definitions_indices(definitions, index_name="by_signature")

    initialised_skill_code = SkillCode(key=12, set=1, group=-99)
    initialised_knowledge_code = KnowledgeCode(key=6, focus=-99, associated_skill=initialised_skill_code)

    get_semantics_from_instance(initialised_knowledge_code, definitions)
