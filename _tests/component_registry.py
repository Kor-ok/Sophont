from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

from colorama import Fore, Style
from colorama import init as colorama_init
from typing_extensions import TypeAlias

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.base import Primitive
from components.data import KnowledgeCode, SkillCode
from utils.terminal import divider, header, highlight

colorama_init(autoreset=True)

DomainIdentity: TypeAlias = int
"""Instead of using the actual class objects as keys in the indices, 
we use their unique integer identities from their subclass_dict. 
This is for a tighter coupling with a DOTS architecture."""

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

def display_base_class_subclass_registry(base_classes: tuple[type, ...]) -> None:
    """Test that the subclass registry is correctly populated for all subclasses of the given base classes."""
    print(f"{Fore.BLUE}Testing subclass registry for base classes: {[base.__name__ for base in base_classes]}...{Style.RESET_ALL}")
    for base in base_classes:
        # Print as a json like dict
        print(f"{Fore.BLUE}{base.__name__}'s Subclass dict: {json.dumps(base.subclass_dict, indent=4)}")

def display_subclass_member_dicts(base_classes: tuple[type, ...]) -> None:
    """Test that the member dict is correctly populated for all subclasses of the given base classes."""
    print(f"{Fore.BLUE}Testing member dict for subclasses of base classes: {[base.__name__ for base in base_classes]}...{Style.RESET_ALL}")
    for base in base_classes:
        for subclass in base.__subclasses__():
            if hasattr(subclass, "member_dict"):
                print(f"{Fore.BLUE}{subclass.__name__}'s Member dict: {json.dumps(subclass.member_dict, indent=4)}{Style.RESET_ALL}")

# ---------------------------------------------------------------------------
# Equality tests
# ---------------------------------------------------------------------------

def test_for_equality_between_collect_module_classes_and_subclass_registry(classes: list[type], base_classes: tuple[type, ...]) -> None:
    """Test that the classes collected from the module match the entries in the subclass registry of the base classes."""
    print(f"{Fore.BLUE}Testing equality between collected classes and subclass registry entries...{Style.RESET_ALL}")
    for base in base_classes:
        for cls in classes:
            if issubclass(cls, base):
                assert cls.__name__ in base.subclass_dict, f"{cls.__name__} is not in {base.__name__}'s subclass registry"
                print(f"{Fore.GREEN}Class {cls.__name__} is correctly registered as a subclass of {base.__name__}.{Style.RESET_ALL}")

def test_for_equality_between_subclass_member_dict_and_class_annotations(classes: list[type]) -> None:
    """Test that the member dict of each class matches the annotations of the class."""
    print(f"{Fore.BLUE}Testing equality between subclass member dict and class annotations...{Style.RESET_ALL}")
    for cls in classes:
        if hasattr(cls, "member_dict"):
            member_dict = cls.member_dict
            annotations = cls.__annotations__
            for index, field_name in member_dict.items():
                assert field_name in annotations, f"{field_name} from {cls.__name__}'s member dict is not in its annotations"
            print(f"{Fore.GREEN}Class {cls.__name__}'s member dict correctly matches its annotations.{Style.RESET_ALL}")

# ---------------------------------------------------------------------------
# Lookups by index
# ---------------------------------------------------------------------------

def get_member_name_by_index(cls: type, index: int) -> str:
    """Helper function to get the member name of a class by its index in the member dict."""
    if hasattr(cls, "member_dict"):
        member_dict = cls.member_dict
        if index in member_dict:
            return member_dict[index]
    raise ValueError(f"Index {index} not found in {cls.__name__}'s member dict")

def get_subclass_name_by_index(base_cls: type, index: DomainIdentity) -> str:
    """Helper function to get the subclass name of a base class by its index in the subclass dict."""
    if hasattr(base_cls, "subclass_dict"):
        subclass_dict = base_cls.subclass_dict
        for subclass_name, subclass_index in subclass_dict.items():
            if subclass_index == index:
                return subclass_name
    raise ValueError(f"Index {index} not found in {base_cls.__name__}'s subclass dict")

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

def get_member_name_by_subclass_index_and_member_index(base_cls: type, subclass_index: DomainIdentity, member_index: int) -> str:
    """Helper function to get the member name of a subclass by the subclass index and member index."""
    subclass_name = get_subclass_name_by_index(base_cls, subclass_index)
    for cls in base_cls.__subclasses__():
        if cls.__name__ == subclass_name:
            return get_member_name_by_index(cls, member_index)
    raise ValueError(f"Subclass with index {subclass_index} not found in {base_cls.__name__}'s subclasses")

# ---------------------------------------------------------------------------
# Lookups by string matches - May return multiple matches since multiple subclasses can have the same member name
# ---------------------------------------------------------------------------

def get_matched_class_indices_from_member_name(base_cls: type, member_name: str) -> tuple[DomainIdentity, ...]:
    """Helper function to get the class of a member name by searching through the 
    subclasses of a base class. Multiple subclasses may have the same member name, 
    so this function returns a tuple of all matching class indices."""
    matched_indices = []
    for subclass in base_cls.__subclasses__():
        if hasattr(subclass, "member_dict"):
            member_dict = subclass.member_dict
            for index, field_name in member_dict.items():
                if field_name == member_name:
                    matched_indices.append(subclass.subclass_dict[subclass.__name__])
    if not matched_indices:
        raise ValueError(f"Member name {member_name} not found in any subclasses of {base_cls.__name__}")
    return tuple(matched_indices)

# ---------------------------------------------------------------------------
# Lookups by post initialised signature
# ---------------------------------------------------------------------------

def display_info_from_signature(signature: tuple[Any, ...], base_cls: type) -> None:
    """Helper function to display the information of a signature by looking up the subclass and member names from the indices."""
    pointer = 0
    while pointer < len(signature) - 1: # -1 to avoid index error if the last value in the signature is a primitive value rather than a domain identity
        domain_identity = signature[pointer]
        subclass = get_subclass_object_by_index(base_cls, domain_identity)
        
        highlight(text=f"Domain identity {domain_identity} corresponds to subclass name: {subclass.__name__}", colour=Fore.GREEN)
        
        highlight(text=f"With members: {list(subclass.member_dict.values())}", colour=Fore.BLUE)
        
        highlight(text=f"Of Member indices: {list(subclass.member_dict.keys())}", colour=Fore.BLUE)
        
        highlight(text=f"And signature values: {signature[pointer + 1 : pointer + 1 + len(subclass.member_dict)]}", colour=Fore.CYAN)
        pointer += len(subclass.member_dict)


if __name__ == "__main__":
    header("TESTING INITIALISED COMPONENT REGISTRY")

    base_classes = (Primitive,)

    classes = collect_module_classes("components.data", base_classes)

    initialised_skill_code = SkillCode(key=21, set=1, group=1)
    initialised_knowledge_code = KnowledgeCode(key=57, focus=-99, associated_skill=initialised_skill_code)

    
    highlight(text=f"'signature' direct from {initialised_knowledge_code}:\n{initialised_knowledge_code.signature}", colour=Fore.GREEN)
    
    highlight(text=f"'member_dict' direct from {initialised_knowledge_code}:\n{initialised_knowledge_code.member_dict}", colour=Fore.BLUE)

    divider()
    EXAMPLE_SIGNATURE: tuple[int, ...] = (2, 57, -99, 1, 21, 1, 1)
    # EXAMPLE_SIGNATURE: tuple[int, ...] = (1, 21, 1, 1)
    header("Example signature to test against:", with_divider=False)
    header(str(EXAMPLE_SIGNATURE))

    display_info_from_signature(EXAMPLE_SIGNATURE, Primitive)