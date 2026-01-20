from __future__ import annotations

import os
import sys

from game.mappings.set import ATTRIBUTES

if sys.stdout.isatty() and "CLEAR_SCREEN" in os.environ:
    print("\033c", end="")



if __name__ == "__main__":
    print("\033c", end="")
    test = (3, 1, 1)
    result = ATTRIBUTES.characteristics.get_aliases(test)
    print(f"Full code for '{test}': {result}")