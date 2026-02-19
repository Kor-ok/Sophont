from __future__ import annotations

import logging
from array import array
from collections.abc import Sequence
from dataclasses import dataclass
from timeit import timeit
from typing import Any, NamedTuple

from colorama import Fore, Style
from colorama import init as colorama_init

from utils.terminal import divider, header

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

colorama_init(autoreset=True, convert=True)

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

def generate_component_signature_via_classes(semantic_map: SemanticMap, semantic_signature: tuple[Any, ...]) -> bytes:
    """Utility function to generate a component signature from a semantic signature using the SemanticMap class."""
    logger.debug(f"Semantic Signature: {Fore.MAGENTA}{semantic_signature}{Style.RESET_ALL}")
    for element in semantic_map.elements:
        logger.debug(f"Depth: {Fore.BLUE}{element.depth}{Style.RESET_ALL}, Domain Identity: {Fore.CYAN}{element.domain_identity}{Style.RESET_ALL}, Pre-Nested Count: {Fore.YELLOW}{element.pre_nested_count}{Style.RESET_ALL}")
    logger.debug("\n")
    logger.debug(f"{Fore.MAGENTA}Generated Component Signature: {Style.RESET_ALL}")
    
    component_signature = []
    seen_depth_and_domain_identity = set()
    semantic_signature_index = 0
    for element in semantic_map.elements:
        if (element.depth, element.domain_identity) not in seen_depth_and_domain_identity:
            component_signature.append(element.domain_identity)
            seen_depth_and_domain_identity.add((element.depth, element.domain_identity))
        component_signature.extend(semantic_signature[semantic_signature_index:semantic_signature_index + element.pre_nested_count])
        semantic_signature_index += element.pre_nested_count
        
    logger.debug(component_signature)
    logger.debug(f"{Fore.GREEN}Expected Component Signature: {Style.RESET_ALL}")
    logger.debug(debug_expected_component_signature)

    # first convert to array of integers, then convert to bytes
    component_signature_array = array('b', component_signature)

    component_signature_bytes = component_signature_array.tobytes()

    return component_signature_bytes

def generate_component_signature_via_itertools(semantic_map_raw: tuple[Any, ...], semantic_signature: tuple[Any, ...]) -> bytes:
    """Utility function to generate a component signature from a semantic signature using itertools."""
    from itertools import chain

    def _flatten_semantic_map_raw(semantic_map_raw: tuple[Any, ...], depth: int = 0, domain_identity: int | None = None) -> list[tuple[int, int, int]]:
        flattened_elements = []
        length_of_raw = len(semantic_map_raw)
        step_though_raw = 0
        while step_though_raw < length_of_raw:
            element_value = semantic_map_raw[step_though_raw]
            if not isinstance(element_value, tuple):
                if step_though_raw == 0:
                    domain_identity = element_value
                else:
                    if domain_identity is not None:
                        flattened_elements.append((depth, domain_identity, element_value))
            elif isinstance(element_value, tuple):
                nested_elements = _flatten_semantic_map_raw(element_value, depth + 1, domain_identity)
                flattened_elements.extend(nested_elements)
            step_though_raw += 1
        return flattened_elements

    flattened_semantic_map = _flatten_semantic_map_raw(semantic_map_raw)
    seen_depth_and_domain_identity = set()
    component_signature = []
    semantic_signature_index = 0
    for depth, domain_identity, pre_nested_count in flattened_semantic_map:
        if (depth, domain_identity) not in seen_depth_and_domain_identity:
            component_signature.append(domain_identity)
            seen_depth_and_domain_identity.add((depth, domain_identity))
        component_signature.extend(semantic_signature[semantic_signature_index:semantic_signature_index + pre_nested_count])
        semantic_signature_index += pre_nested_count

    # first convert to array of integers, then convert to bytes
    component_signature_array = array('b', component_signature)
    component_signature_bytes = component_signature_array.tobytes()
    return component_signature_bytes

if __name__ == '__main__':
    header("Prototype Testing")

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

    semantic_mapping_times = []
    generate_via_classes_times = []
    generate_via_itertools_times = []

    for key, (semantic_map_raw, semantic_signature, debug_expected_component_signature) in _semantic_map_data.items():
        print(f"{Fore.WHITE}{key}:{Style.RESET_ALL}\n")
        print(f"Semantic Signature:            {Fore.BLUE}{semantic_signature}{Style.RESET_ALL}")

        print("\nVia OOP Classes:")
        generated_component_signature_via_classes = generate_component_signature_via_classes(generated_semantic_maps[key], semantic_signature)
        # first convert the generated component signature to array of integers, then convert to tuples for easier comparison
        generated_component_signature_array = array('b', generated_component_signature_via_classes)
        generated_component_signature_tuple = tuple(generated_component_signature_array)
        print(f"{Fore.GREEN}Generated Component Signature: {Style.RESET_ALL}{generated_component_signature_tuple}")
        # first convert the expected component signature to array of integers, then convert to bytes for comparison
        expected_component_signature_array = array('b', debug_expected_component_signature)
        debug_expected_component_signature_bytes = expected_component_signature_array.tobytes()
        print(f"{Fore.YELLOW}Expected Component Signature:  {Style.RESET_ALL}{debug_expected_component_signature}")
        try:
            assert generated_component_signature_via_classes == debug_expected_component_signature_bytes
            print(f"{Fore.GREEN}Test Passed!{Style.RESET_ALL}")
        except AssertionError:
            print(f"{Fore.RED}Test Failed!{Style.RESET_ALL}")

        print("\nVia Itertools:")
        generated_component_signature_via_itertools = generate_component_signature_via_itertools(semantic_map_raw, semantic_signature)
        # first convert the generated component signature to array of integers, then convert to tuples for easier comparison
        generated_component_signature_array = array('b', generated_component_signature_via_itertools)
        generated_component_signature_tuple = tuple(generated_component_signature_array)
        print(f"{Fore.GREEN}Generated Component Signature: {Style.RESET_ALL}{generated_component_signature_tuple}")
        # first convert the expected component signature to array of integers, then convert to bytes for comparison
        expected_component_signature_array = array('b', debug_expected_component_signature)
        debug_expected_component_signature_bytes = expected_component_signature_array.tobytes()
        print(f"{Fore.YELLOW}Expected Component Signature:  {Style.RESET_ALL}{debug_expected_component_signature}")
        try:
            assert generated_component_signature_via_itertools == debug_expected_component_signature_bytes
            print(f"{Fore.GREEN}Test Passed!{Style.RESET_ALL}")
        except AssertionError:
            print(f"{Fore.RED}Test Failed!{Style.RESET_ALL}")

        print("\n" + "-"*80 + "\n")

        semantic_map_time = timeit(lambda: generate_semantic_map_via_classes(semantic_map_raw), number=1000)
        classes_time = timeit(lambda: generate_component_signature_via_classes(generated_semantic_maps[key], semantic_signature), number=1000)
        itertools_time = timeit(lambda: generate_component_signature_via_itertools(semantic_map_raw, semantic_signature), number=1000)
        logger.debug(f"{Fore.MAGENTA}Generating Semantic Map: {semantic_map_time:.6f} seconds{Style.RESET_ALL}")
        logger.debug(f"{Fore.BLUE}Via OOP Classes: {classes_time:.6f} seconds{Style.RESET_ALL}")
        logger.debug(f"{Fore.CYAN}Via Itertools:   {itertools_time:.6f} seconds{Style.RESET_ALL}")

        semantic_mapping_times.append(semantic_map_time)
        generate_via_classes_times.append(classes_time)
        generate_via_itertools_times.append(itertools_time)

    header("Performance Testing")
    average_semantic_mapping_time = sum(semantic_mapping_times) / len(semantic_mapping_times)
    average_generate_via_classes_time = sum(generate_via_classes_times) / len(generate_via_classes_times)
    
    print(f"{Fore.BLUE}Average Time Via OOP Classes: {(average_semantic_mapping_time + average_generate_via_classes_time):.6f} seconds{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Average Time Via Itertools:   {sum(generate_via_itertools_times) / len(generate_via_itertools_times):.6f} seconds{Style.RESET_ALL}")


    if (average_semantic_mapping_time + average_generate_via_classes_time) < (sum(generate_via_itertools_times) / len(generate_via_itertools_times)):
        print(f"{Fore.GREEN}OOP Classes win!{Style.RESET_ALL}")
    elif (average_semantic_mapping_time + average_generate_via_classes_time) > (sum(generate_via_itertools_times) / len(generate_via_itertools_times)):
        print(f"{Fore.GREEN}Itertools win!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}It's a tie!{Style.RESET_ALL}")