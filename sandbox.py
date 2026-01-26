from __future__ import annotations

from pympler import asizeof

from game.mappings.set import ATTRIBUTES
from gui.initialisation.species import example_sophont_1

if __name__ == "__main__":

    # print("\033c", end="")
    memory_footprint = asizeof.asizeof(example_sophont_1)
    print(f"Memory footprint of ATTRIBUTES: {memory_footprint} bytes")

    example_data = example_sophont_1.name
    print(f"Example Sophont Name: {example_data}")