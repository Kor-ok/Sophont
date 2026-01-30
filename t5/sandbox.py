"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support

def main() -> None:
    """Run all demonstrations."""
    print("Demo")
    print("=" * 60)
    print()
    

    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
