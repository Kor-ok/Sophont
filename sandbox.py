from __future__ import annotations

import inspect
import math
from collections.abc import Iterable
from pprint import pprint
from timeit import timeit
from typing import Optional

from colorama import Fore, Style
from colorama import init as colorama_init
from pympler.asizeof import asizeof

from semantics.data import KnowledgeCode, SkillCode
from utils.dev import CACHE_SIZES

colorama_init(autoreset=True, convert=True)  # Initialize colorama for colored output in the terminal



def main() -> None:
    example_tuple = (13, 11, 9, 7, 5, 3, 1)
    print(f"Original tuple: {example_tuple}\n")
    length_per_subset = [
         3,  # First subset will have 3 elements
         3,  # Second subset will have 3 elements
    ]
    subsets = []
    pointer = 0
    subset_index = 0
    subset_count = len(length_per_subset)
    while pointer < len(example_tuple) and subset_index < subset_count:
        print(f"\nsubset_index % subset_count: {subset_index % subset_count}")
        current_length = length_per_subset[subset_index % subset_count]
        print(f"Current subset length: {current_length}")
        subset_index += 1
        print(f"Subset index after increment: {subset_index}")
        slice_start = pointer
        slice_end = pointer + current_length
        sliced_values = example_tuple[slice_start:slice_end]
        print(f"Sliced values: {sliced_values} using slice indices [{slice_start}:{slice_end}]")
        subsets.append(sliced_values)
        pointer += current_length
        if pointer + current_length > len(example_tuple):
            break  # Avoid slicing beyond the end of the tuple

    print(f"\nAll subsets: {subsets}")




if __name__ == '__main__':
	# main()
    print(f"KnowledgeCode.member_dict length: {len(KnowledgeCode.member_dict)}")
    print(f"{KnowledgeCode.member_dict}")
    print(f"SkillCode.member_dict length: {len(SkillCode.member_dict)}")
    print(f"{SkillCode.member_dict}")