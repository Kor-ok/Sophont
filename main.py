from __future__ import annotations

import runpy
import sys
from pathlib import Path


def _main() -> None:
    # Ensure the project root is on sys.path so relative imports inside
    # uielement_character_card.py work as expected, then run it as a script.
    script_path = Path(__file__).resolve().parent / "uielement_character_card.py"
    sys.path.insert(0, str(script_path.parent))
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    _main()

