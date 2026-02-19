from __future__ import annotations

import inspect
import json
import logging
from array import array
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple, Union, get_type_hints

from colorama import Fore, Style
from colorama import init as colorama_init

from semantics.data import CharacteristicCode, KnowledgeCode, SkillCode, TestComplexComponent
from utils.terminal import divider, header

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

colorama_init(autoreset=True, convert=True)  # Initialize colorama for colored output in the terminal

def display_dict(data: dict) -> None:
    """Utility function to reparse the data into types that a json encoder can handle."""
    # keys must be str, int, float, bool or None, not type
    reparsed_data = {}
    for key, value in data.items():
        # stringify everything
        key = str(key)
        value = str(value)
        reparsed_data[key] = value

    print(json.dumps(reparsed_data, indent=4))

def test_instantiated_components():
    """Test the semantics of instantiated components."""
    test_classes = [
        _skill := SkillCode(21, 1, -99),
        _knowledge := KnowledgeCode(41, -99, _skill),
        _characteristic := CharacteristicCode(1, 0, 1),
        _test_complex := TestComplexComponent(6, _characteristic, 4, 3, _knowledge, 1),
        ]
    for cls in test_classes:
        print(f"{Fore.CYAN}Testing class: {cls.__class__.__name__}{Style.RESET_ALL}")
        domain_identity = cls.domain_identity
        component_signature = cls.component_signature
        semantic_signature = cls.semantic_signature
        cache_key = cls._cache_key()
        print(f"Domain Identity: {Fore.YELLOW}{domain_identity}")
        print(f"Component Signature: {component_signature}")
        print(f"Semantic Signature: {semantic_signature}")
        print(f"Cache Key: {cache_key}")    

def test_class_level_components():
    """Test the semantics of class-level components."""
    test_classes = [
        SkillCode,
        KnowledgeCode,
        CharacteristicCode,
        TestComplexComponent,
        ]
    for cls in test_classes:
        print(f"{Fore.CYAN}Testing class: {cls.__name__}{Style.RESET_ALL}")
        member_dict = cls.member_dict
        display_dict(member_dict)

def test_semantic_map():
    test_classes: dict[type, tuple[Any, ...]] = { # class to test: expected semantic map
        CharacteristicCode: (0, 3),
        SkillCode: (1, 3),
        KnowledgeCode: (2, 2, (1, 3)),
        TestComplexComponent: (4, 1, (0, 3), 2, ((2, 2, (1, 3))), 1),
    }
    for cls, expected_semantic_map in test_classes.items():
        print(f"{Fore.CYAN}Testing class: {cls.__name__}{Style.RESET_ALL}")
        semantic_map = _generate_semantic_map(cls)
        print(f"Semantic Map: {Fore.GREEN}{semantic_map}{Style.RESET_ALL}")
        try:
            assert semantic_map == expected_semantic_map
            print(f"{Fore.GREEN}Test passed!{Style.RESET_ALL}")
        except AssertionError:
            print(f"{Fore.RED}Test failed! Expected: {expected_semantic_map}, Got: {semantic_map}{Style.RESET_ALL}")
        print("\n" + "-"*80 + "\n")

def test_byte_component_signatures():
    test_classes = [
        _skill := SkillCode(21, 1, -99),
        _knowledge := KnowledgeCode(41, -99, _skill),
        _characteristic := CharacteristicCode(1, 0, 1),
        _test_complex := TestComplexComponent(6, _characteristic, 4, 3, _knowledge, 1),
        ]
    for cls in test_classes:
        print(f"{Fore.CYAN}Testing class: {cls.__class__.__name__}{Style.RESET_ALL}")
        component_signature_from_property = cls._component_signature()
        component_signature_from_class_level = cls.component_signature
        _converted = array('b', component_signature_from_class_level)
        print(f"Component Signature from property: {component_signature_from_property}")
        print(f"Converted Component Signature: {_converted}")
        try:
            assert component_signature_from_property == _converted
            print(f"{Fore.GREEN}Test passed!{Style.RESET_ALL}")
        except AssertionError:
            print(f"{Fore.RED}Test failed! Expected: {_converted}, Got: {component_signature_from_property}{Style.RESET_ALL}")

def _generate_semantic_map(cls: type, recursion: int = 0) -> tuple[Any, ...]:
    if recursion > 2:
        raise RecursionError(f"Recursion limit exceeded while generating semantic map for {cls.__name__}. This may indicate a circular reference in the class definitions.")
    """
    class TestComplexComponent:
        field1: int
        field2: semantics.data.CharacteristicCode
        field3: int
        field4: int
        field5: semantics.data.KnowledgeCode
        field6: int

    Example: for a ``TestComplexComponent`` with the above fields, the result is

    Semantic Map = (4, 1, (0, 3), 2, ((2, 2, (1, 3))), 1)
                    ↑  ↑   ↑      ↑    ↑      ↑        ↑
                    a  b   c      d    e      f        g
    where:
    a: the subclass index for TestComplexComponent in its subclass_dict
    b: the number of fields before the first field of type in domain_map (field1)
    c: the semantic map for the nested class CharacteristicCode (field2)
    d: the number of fields between the first field of type in domain_map and the
       second field of type in domain_map (field3 and field4)
    e: the semantic map for the nested class KnowledgeCode (field5)
    f: the deeper semantic map for SkillCode inside KnowledgeCode (field5)
    g: the number of fields after the last field of type in domain_map (field6) 
    """
    domain_map = cls.subclass_dict
    filtered_members = _filter_type_hints(cls)
    if recursion == 0:
        display_dict(filtered_members)
    semantic_map = (cls.subclass_dict[cls],)

    def _recursive_member_identity_search() -> tuple[int, Union[type, None], bool]:
        nonlocal member_position
        items = list(filtered_members.items())
        count = 0
        nested_with = None

        while member_position < number_of_members:
            name, t = items[member_position]
            member_position += 1
            if t in domain_map:
                nested_with = t
                return count, nested_with, member_position >= number_of_members
            count += 1

        return count, None, True
    member_position = 0
    number_of_members = len(filtered_members)
    
    # Count the number of fields in filtered_members in order before the first
    # field of type in domain_map
    while member_position < number_of_members:
        
        count, nested, finished = _recursive_member_identity_search()
        print(f"Position: {Fore.GREEN}{member_position}{Style.RESET_ALL}, Count: {Fore.YELLOW}{count}{Style.RESET_ALL}, Nested: {Fore.GREEN if nested else Fore.BLUE}{nested}{Style.RESET_ALL}, Finished: {Fore.RED if finished else Fore.GREEN}{finished}{Style.RESET_ALL}")
        if not nested and finished:
            semantic_map += (count,)
            break
        elif nested: # nested and not finished: nested and finished:
            nested_result = _generate_semantic_map(nested, recursion + 1)
            semantic_map += (count, (nested_result),)
        else: # not nested and not finished
            print(f"{Fore.RED}Unexpected case: not nested and not finished. This should not happen.{Style.RESET_ALL}")
            semantic_map += (count,)
        
    return semantic_map

def _filter_type_hints(cls: type) -> Any:
    base_class = cls.mro()[-2]
    subclasses = base_class.subclass_dict
    type_hints = get_type_hints(cls)
    filtered_type_hints = {}
    for name, type in type_hints.items():
        if name not in ("subclass_dict", "member_dict", "component_signature", "semantic_signature"):
            if type in (int, float, bool) or type in subclasses:
                filtered_type_hints[name] = type
    return filtered_type_hints

def _convert_nested_tuples_to_nested_array(nested_tuple: tuple[Any, ...]) -> array:
    """Utility function to convert nested tuples to nested arrays.
    If the input is a tuple of ints, it converts it to an array of ints.
    """
    if isinstance(nested_tuple, tuple) and all(isinstance(x, int) for x in nested_tuple):
        return array('b', nested_tuple)
    elif isinstance(nested_tuple, tuple):
        return tuple(_convert_nested_tuples_to_nested_array(x) for x in nested_tuple)
    else:
        return nested_tuple

class SemanticMapElement(NamedTuple):
        depth: int
        domain_identity: int
        pre_nested_count: int

@dataclass
class SemanticMap:
    elements: Sequence[SemanticMapElement]

def _semantic_map_from_raw(semantic_map_raw: tuple[Any, ...], depth: int = 0) -> list[SemanticMapElement]:
        
    semantic_map_elements: list[SemanticMapElement] = []

    length_of_raw = len(semantic_map_raw)
    step_though_raw = 0
    domain_identity = None
    while step_though_raw < length_of_raw:
        element_value = semantic_map_raw[step_though_raw]
        if not isinstance(element_value, tuple):
            if step_though_raw == 0:
                domain_identity = element_value
            else:
                if domain_identity is not None:
                    semantic_map_elements.append(SemanticMapElement(depth=depth, domain_identity=domain_identity, pre_nested_count=element_value))
        elif isinstance(element_value, tuple):
            nested_elements = _semantic_map_from_raw(element_value, depth + 1)
            semantic_map_elements.extend(nested_elements)
        step_though_raw += 1
    
    return semantic_map_elements

def generate_semantic_map_via_classes(semantic_map_raw: tuple[Any, ...]) -> SemanticMap:
    """Utility function to generate a semantic map from a raw semantic map tuple."""
    semantic_map_elements = _semantic_map_from_raw(semantic_map_raw)
    return SemanticMap(elements=semantic_map_elements)

def generate_component_signature_via_classes(semantic_map: SemanticMap, semantic_signature: tuple[Any, ...]) -> None:
    """Utility function to generate a component signature from a semantic signature using the SemanticMap class."""
    print(f"Semantic Signature: {Fore.MAGENTA}{semantic_signature}{Style.RESET_ALL}")
    for element in semantic_map.elements:
        print(f"Depth: {Fore.BLUE}{element.depth}{Style.RESET_ALL}, Domain Identity: {Fore.CYAN}{element.domain_identity}{Style.RESET_ALL}, Pre-Nested Count: {Fore.YELLOW}{element.pre_nested_count}{Style.RESET_ALL}")
    print("\n")
    print(f"{Fore.MAGENTA}Generated Component Signature: {Style.RESET_ALL}")
    
    component_signature = []
    seen_depth_and_domain_identity = set()
    semantic_signature_index = 0
    for element in semantic_map.elements:
        if (element.depth, element.domain_identity) not in seen_depth_and_domain_identity:
            component_signature.append(element.domain_identity)
            seen_depth_and_domain_identity.add((element.depth, element.domain_identity))
        component_signature.extend(semantic_signature[semantic_signature_index:semantic_signature_index + element.pre_nested_count])
        semantic_signature_index += element.pre_nested_count
        
    print(component_signature)
    print(f"{Fore.GREEN}Expected Component Signature: {Style.RESET_ALL}")
    print(debug_expected_component_signature)


if __name__ == '__main__':
    header("Sandbox")
    print(f"{Fore.YELLOW}This is a sandbox for testing and experimentation. It is not intended for production use.{Style.RESET_ALL}")
    divider()

    _semantic_map_data = {    
        "_characteristic_semantic_map_data": [
            semantic_map_raw :=                   (0, 3),
            semantic_signature :=                    (1, 0, 1),
            debug_expected_component_signature := (0, 1, 0, 1),
        ],

        "_knowledge_semantic_map_data": [
            semantic_map_raw :=                   (2, 2,      (1, 3)),
            semantic_signature :=                    (15, -99,    59, 5, 1),
            debug_expected_component_signature := (2, 15, -99, 1, 59, 5, 1),
        ],

        "_testcomplexcomponent_semantic_map_data": [
            semantic_map_raw :=                   (4, 1, (0, 3),      2,  ((2, 2,      (1, 3))),       1),
            semantic_signature :=                    (6,     1, 0, 1, 4, 3,    41, -99,    21, 1, -99, 1),
            debug_expected_component_signature := (4, 6,  0, 1, 0, 1, 4, 3, 2, 41, -99, 1, 21, 1, -99, 1),
        ],
    }

    generated_semantic_maps = {}
    for key, (semantic_map_raw, semantic_signature, debug_expected_component_signature) in _semantic_map_data.items():
        generated_semantic_map: SemanticMap = generate_semantic_map_via_classes(semantic_map_raw)
        generated_semantic_maps[key] = generated_semantic_map
        
    divider()
    print("\n" + "-"*80 + "\n")

    for key, (semantic_map_raw, semantic_signature, debug_expected_component_signature) in _semantic_map_data.items():
        print(f"{Fore.WHITE}{key}:{Style.RESET_ALL}")
        print(f"Raw: {Fore.BLUE}{semantic_map_raw}{Style.RESET_ALL}\n")
        generated_component_signature = generate_component_signature_via_classes(generated_semantic_maps[key], semantic_signature)
        print("\n" + "-"*80 + "\n")