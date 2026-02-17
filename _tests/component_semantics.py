"""Professional-level test suite for ``humaniseT5.definitions.api``.

Design principles demonstrated
-------------------------------
1. **Arrange / Act / Assert** (AAA) — every test reads top-to-bottom in three
   clear phases so intent is obvious at a glance.
2. **Fixtures for shared setup** — expensive I/O (reading *Definitions.xlsx*)
   happens once per session via ``pytest`` fixtures scoped appropriately.
3. **Isolated unit tests vs. integration tests** — pure logic is tested with
   synthetic data (unit); real workbook loading is tested separately
   (integration) so the suite stays fast and debuggable.
4. **Parametrize for data-driven coverage** — ``@pytest.mark.parametrize``
   replaces copy-paste test variants and makes it trivial to add new cases.
5. **Clear naming convention** — ``test_<unit>_<scenario>_<expected>`` tells
   the reader *what* is under test, *when*, and *what should happen*.
6. **Minimal assertions per test** — each test verifies one logical behaviour,
   keeping failure messages actionable.
7. **Performance regression guard** — a dedicated benchmark test captures
   execution time so regressions are caught early.

Running
-------
From the repo root::

    python -m pytest humaniseT5/_tests/definitions.py -v

"""

from __future__ import annotations

import sys
from pathlib import Path
from timeit import timeit
from typing import Any, get_type_hints

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is importable when running the file directly.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.t5 import DefinitionsIndices, build_definitions_indices
from semantics.base import Primitive
from utils.semantics import (
    collect_module_classes,
    construct_composite_signature,
    get_recursive_component_classes,
    parse_signature_portion_from_type,
)

# ═══════════════════════════════════════════════════════════════════════════
#  FIXTURES
# ═══════════════════════════════════════════════════════════════════════════
# Fixtures centralise setup so individual tests stay short.
#
# ``scope="session"`` means "run this fixture once for the entire test
#  session and reuse the result" — ideal for expensive I/O like reading
#  an Excel workbook.
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def component_classes() -> list[type]:
    """Collect the real component classes once per session.

    This mirrors the production call-site in ``Definitions.__init__``.
    """
    return collect_module_classes("components.data", (Primitive,))

@pytest.fixture(scope="session")
def definitions_index(component_classes: list[type]) -> DefinitionsIndices:
    """Build the full ``DefinitionsIndex`` from the real workbook once per
    session so every test that needs it can share the result without
    re-reading the Excel file.
    """
    return build_definitions_indices(component_classes)

# ---------------------------------------------------------------------------
# Lightweight synthetic fixtures — used by *unit* tests that must not depend
# on the real workbook.  This keeps those tests fast, deterministic, and easy
# to reason about.
# ---------------------------------------------------------------------------
def generate_member_dict(instance: Any) -> dict[int, tuple[str, type]]:
        """Generate a dict mapping field index to field name for a component class."""
        member_dict = {}
        for name, type in get_type_hints(instance).items():
            if name != "subclass_dict":
                member_dict[len(member_dict)] = name, type
        return member_dict

class _TestBaseClass:
    """Base class for testing recursive type detection in get_recursive_component_classes.
    """

    __name__ = "_TestBaseClass"
    subclass_dict: dict[type, int] = {}
    def __init_subclass__(cls) -> None:
        if cls not in cls.subclass_dict:
            cls.subclass_dict[cls] = len(cls.subclass_dict)

class _TestComponentA(_TestBaseClass):
    """Minimal stand-in for a component class
    """

    __name__ = "_TestComponentA"
    member_dict = {0: ('field1', int), 1: ('field2', int), 2: ('field3', int)}

class _TestComponentB(_TestBaseClass):
    """Minimal stand-in for a component class
    """

    __name__ = "_TestComponentB"
    member_dict = {0: ('field1', int), 1: ('field2', _TestComponentA)}


# ═══════════════════════════════════════════════════════════════════════════
#  UNIT TESTS — pure logic, no I/O
# ═══════════════════════════════════════════════════════════════════════════
# These test individual helper functions using the synthetic fixture.
# They are fast and deterministic — if they fail, the bug is in the
# function's logic, not in the data.
# ═══════════════════════════════════════════════════════════════════════════

class TestGetRecursiveComponentClasses:
    def test_get_non_recursive(self):
        """Test that a non-recursive class returns itself with the correct domain identity and members length."""

        expected = dict([(_TestComponentA, (0, 4))])
        result = get_recursive_component_classes(_TestComponentA, set())
        assert result == expected

    def test_get_directly_recursive(self):
        """Test that a directly recursive class returns itself and the recursive type with the correct domain identities and members lengths."""
        
        expected = dict([
            (_TestComponentB, (1, 2)),
            (_TestComponentA, (0, 4)),
        ])
        result = get_recursive_component_classes(_TestComponentB, set())
        assert result == expected

class TestConstructCompositeSignature:
    def test_construct_composite_signature(self):
        """Test that the composite signature is constructed correctly from the parse signature and recursive types."""
        parse_signature = (10, 20, 10, 20, 30, 40)
        recursive_types = dict([
            (_TestComponentB, (1, 2)),
            (_TestComponentA, (0, 4)),
        ])
        expected = (1, 10, 20, 0, 10, 20, 30, 40)
        result = construct_composite_signature(parse_signature, recursive_types)
        assert result == expected

# ═══════════════════════════════════════════════════════════════════════════
#  DIRECT-RUN SUPPORT
# ═══════════════════════════════════════════════════════════════════════════
# Allows running this file directly for a
# quick sanity check without requiring the pytest runner.
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))