from __future__ import annotations

import os
import sys

from game.mappings import KNOWLEDGES_FULL_CODE_TO_STR_ALIASES
from game.mappings.set import ATTRIBUTES

if sys.stdout.isatty() and "CLEAR_SCREEN" in os.environ:
    print("\033c", end="")

if __name__ == "__main__":
    print("\033c", end="") # Note this will confuse CoPilot agents when they try to read stdout.
    test_knowledge_name = "grav (12)"
    result_code = ATTRIBUTES.knowledges.get_full_code(test_knowledge_name)
    print(result_code)

    # print(KNOWLEDGES_FULL_CODE_TO_STR_ALIASES)