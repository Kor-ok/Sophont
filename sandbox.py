from __future__ import annotations

import inspect
import json
import math
from collections import OrderedDict
from collections.abc import Iterable
from pprint import pprint
from timeit import timeit
from typing import Optional, get_type_hints

from colorama import Fore, Style
from colorama import init as colorama_init
from pympler.asizeof import asizeof
from typing_extensions import TypeAlias

from semantics.base import Primitive
from semantics.data import CharacteristicCode, GenderCode, KnowledgeCode, SkillCode
from utils.dev import CACHE_SIZES
from utils.terminal import divider, header

colorama_init(autoreset=True, convert=True)  # Initialize colorama for colored output in the terminal
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
                    # This needs to be at the top of the ordered dict
                    recursive_types[cls] = (primary_domain_identity, self_members_length) # Keep the existing members length for the initial class to allow for self recursion without including the domain identity in the member count for that initial class
    else:
        # We only add itself to the recursive types
        recursive_types[cls] = (primary_domain_identity, len(cls.member_dict) + 1) # Add +1 to account for the domain identity at the start of the signature for each class
    
    if not recursive_types:
        raise ValueError(f"No recursive types found for class {cls.__name__}.")
    return recursive_types

if __name__ == '__main__':
    # header("Base Class Subclass Dict")
    # print(f"Primitive.subclass_dict: {Primitive.subclass_dict}")

    # header("Subclass member dicts")
    # print(f"KnowledgeCode.member_dict length: {len(KnowledgeCode.member_dict)}")
    # print(f"{KnowledgeCode.member_dict}")
    # print(f"SkillCode.member_dict length: {len(SkillCode.member_dict)}")
    # print(f"{SkillCode.member_dict}")

    # header("Fetching subclass_dict from subclass")
    # print(f"KnowledgeCode.subclass_dict: {KnowledgeCode.subclass_dict}")

    header("Recursive Type Check")
    types_to_check = [KnowledgeCode, SkillCode, CharacteristicCode, GenderCode]
    recursion_results = {}
    for type_to_check in types_to_check:
        recursive_types = return_recursive_types(type_to_check)
        recursion_results[type_to_check] = recursive_types
    

    # header("Component Signatures")
    # initialised_skill_code = SkillCode(key=12, set=1, group=-99)
    # print(f"Signature for {initialised_skill_code}: {initialised_skill_code.signature}")
    # initialised_knowledge_code = KnowledgeCode(key=6, focus=-99, associated_skill=initialised_skill_code)
    # print(f"Signature for {initialised_knowledge_code}: {initialised_knowledge_code.signature}")