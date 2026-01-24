from __future__ import annotations

from pympler import asizeof

from game.mappings.set import ATTRIBUTES

if __name__ == "__main__":

    # print("\033c", end="")
    memory_footprint = asizeof.asizeof(ATTRIBUTES)
    print(f"Memory footprint of ATTRIBUTES: {memory_footprint} bytes")
