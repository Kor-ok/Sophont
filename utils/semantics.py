from __future__ import annotations

import logging
from collections import OrderedDict
from importlib import import_module
from typing import Any, Optional

logger = logging.getLogger(__name__)


def return_recursive_types(
    cls: type,
    seen: Optional[set[type]] = None
) -> OrderedDict[type, tuple[int, int]]:
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

def construct_composite_signature(parse_signature: tuple[int, ...], recursive_types: dict[type, tuple[int, int]]) -> tuple[int, ...]:
    """Construct a composite signature by adding the domain identity at the start of the parse signature tuple, to create a unique key for the by_signature index."""
    composite_signature: tuple[int, ...] = ()
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

def parse_signature_portion_from_type(cls: type, primary_signature: tuple[int, ...]) -> tuple[int, ...]:
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
