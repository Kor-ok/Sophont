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
from collections import OrderedDict
from pathlib import Path
from timeit import timeit

import pytest
from numpy import int8

# ---------------------------------------------------------------------------
# Ensure the project root is importable when running the file directly.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.t5 import (
    build_definitions_indices,
)
from utils.semantics import collect_module_classes

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
def component_classes() -> dict[type, ComponentClassInfo]:
    """Collect the real component classes once per session.

    This mirrors the production call-site in ``Definitions.__init__``.
    """
    return collect_module_classes("components.data", (Primitive,))


@pytest.fixture(scope="session")
def definitions_index(component_classes: dict[type, ComponentClassInfo]) -> DefinitionsIndex:
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


class _FakeDomain:
    """Minimal stand-in for a component class when we only care about
    dict-key identity.
    """

    __name__ = "_FakeDomain"


@pytest.fixture()
def synthetic_index() -> DefinitionsIndex:
    """Builds a tiny, deterministic ``DefinitionsIndex`` from hand-crafted
    data.  Lets us test lookup helpers in complete isolation from I/O.
    """
    sig_attr = ComponentAttributeInfo(name="signature", signature=(int8(1), int8(0), int8(1)))
    field_attr = ComponentAttributeInfo(name="subtype", signature=(int8(0),))

    by_signature: OrderedDict = OrderedDict()
    by_signature[(_FakeDomain, sig_attr)] = {"strength": ("str", "stren")}

    by_alias: OrderedDict = OrderedDict()
    by_alias[(_FakeDomain, "strength")] = sig_attr
    by_alias[(_FakeDomain, "str")] = sig_attr
    by_alias[(_FakeDomain, "stren")] = sig_attr
    by_alias[(_FakeDomain, "subtype_default")] = field_attr

    return DefinitionsIndex(by_signature=by_signature, by_alias=by_alias)


# ═══════════════════════════════════════════════════════════════════════════
#  UNIT TESTS — pure logic, no I/O
# ═══════════════════════════════════════════════════════════════════════════
# These test individual helper functions using the synthetic fixture.
# They are fast and deterministic — if they fail, the bug is in the
# function's logic, not in the data.
# ═══════════════════════════════════════════════════════════════════════════


class TestGetAliasMapBySignature:
    """Tests for ``get_alias_map_by_signature``."""

    def test_known_signature_returns_alias_map(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN a signature that exists in the index
        WHEN we look it up
        THEN we get back a non-None alias map with the expected canonical key.
        """
        # Arrange
        sig = (int8(1), int8(0), int8(1))

        # Act
        result = get_alias_map_by_signature(_FakeDomain, sig, synthetic_index)

        # Assert
        assert result is not None, "Expected a match for a known signature"
        assert "strength" in result

    def test_unknown_signature_returns_none(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN a signature that does *not* exist
        WHEN we look it up
        THEN None is returned (no KeyError, no crash).
        """
        result = get_alias_map_by_signature(
            _FakeDomain, (int8(99), int8(99), int8(99)), synthetic_index
        )
        assert result is None

    def test_wrong_class_returns_none(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN a valid signature but for a different class
        WHEN we look it up
        THEN None is returned — lookups are class-scoped.
        """

        class _OtherDomain:
            pass

        result = get_alias_map_by_signature(
            _OtherDomain, (int8(1), int8(0), int8(1)), synthetic_index
        )
        assert result is None


class TestGetAttributeByName:
    """Tests for ``get_attribute_by_name``."""

    def test_canonical_name_returns_attribute(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN the canonical name 'strength'
        WHEN we look it up
        THEN we receive the correct ``ComponentAttributeInfo``.
        """
        result = get_attribute_by_name(_FakeDomain, "strength", synthetic_index)
        assert result is not None
        assert result.name == "signature"
        assert result.signature == (int8(1), int8(0), int8(1))

    @pytest.mark.parametrize("alias", ["str", "stren"])
    def test_alias_name_returns_same_attribute(
        self,
        alias: str,
        synthetic_index: DefinitionsIndex,
    ) -> None:
        """GIVEN an alias for 'strength'
        WHEN we look it up
        THEN we get the same attribute info as the canonical name.

        ``@pytest.mark.parametrize`` runs this test once per alias value,
        so adding coverage for a new alias is a one-line change.
        """
        canonical = get_attribute_by_name(_FakeDomain, "strength", synthetic_index)
        result = get_attribute_by_name(_FakeDomain, alias, synthetic_index)
        assert result == canonical

    def test_name_lookup_is_case_insensitive(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN mixed-case input like 'Strength' or 'STRENGTH'
        WHEN we look it up
        THEN it resolves identically to the lowercase form.

        This validates that ``lowercase_and_strip`` is applied internally.
        """
        lower = get_attribute_by_name(_FakeDomain, "strength", synthetic_index)
        upper = get_attribute_by_name(_FakeDomain, "STRENGTH", synthetic_index)
        mixed = get_attribute_by_name(_FakeDomain, "Strength", synthetic_index)
        assert lower == upper == mixed

    def test_unknown_name_returns_none(self, synthetic_index: DefinitionsIndex) -> None:
        """GIVEN a name that has no entry
        WHEN we look it up
        THEN None is returned.
        """
        result = get_attribute_by_name(_FakeDomain, "nonexistent_attribute", synthetic_index)
        assert result is None

    def test_leading_trailing_whitespace_is_stripped(
        self,
        synthetic_index: DefinitionsIndex,
    ) -> None:
        """GIVEN a name with extraneous whitespace
        WHEN we look it up
        THEN the lookup still succeeds (whitespace is stripped).
        """
        result = get_attribute_by_name(_FakeDomain, "  strength  ", synthetic_index)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════
#  DATA-TYPE / CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════════
# These validate the structural contracts of types defined in api.py.
# ═══════════════════════════════════════════════════════════════════════════


class TestComponentAttributeInfo:
    """Ensure ``ComponentAttributeInfo`` behaves as a well-formed NamedTuple."""

    def test_is_named_tuple(self) -> None:
        info = ComponentAttributeInfo(name="test", signature=(int8(1),))
        assert hasattr(info, "_fields"), "ComponentAttributeInfo should be a NamedTuple"

    def test_fields_are_accessible_by_name(self) -> None:
        info = ComponentAttributeInfo(name="subtype", signature=(int8(0),))
        assert info.name == "subtype"
        assert info.signature == (int8(0),)

    def test_equality_by_value(self) -> None:
        """NamedTuples compare by value, not identity.  This is fundamental
        for their use as dict keys in the index.
        """
        a = ComponentAttributeInfo(name="x", signature=(int8(1),))
        b = ComponentAttributeInfo(name="x", signature=(int8(1),))
        assert a == b
        assert a is not b  # distinct objects but equal

    def test_usable_as_dict_key(self) -> None:
        """Since the forward index uses ``ComponentAttributeInfo`` inside
        composite keys, it must be hashable.
        """
        info = ComponentAttributeInfo(name="x", signature=(int8(1),))
        d = {info: "value"}
        assert d[info] == "value"


class TestDefinitionsIndex:
    """Ensure ``DefinitionsIndex`` upholds its contract."""

    def test_is_named_tuple_with_two_fields(self) -> None:
        idx = DefinitionsIndex(by_signature=OrderedDict(), by_alias=OrderedDict())
        assert idx._fields == ("by_signature", "by_alias")

    def test_empty_index_returns_none_for_any_lookup(self) -> None:
        """An empty index should not crash — lookups simply return ``None``."""
        empty = DefinitionsIndex(by_signature=OrderedDict(), by_alias=OrderedDict())
        assert get_alias_map_by_signature(_FakeDomain, (int8(0),), empty) is None
        assert get_attribute_by_name(_FakeDomain, "anything", empty) is None


# ═══════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS — real workbook
# ═══════════════════════════════════════════════════════════════════════════
# These read the actual Definitions.xlsx via the session-scoped fixture.
# They verify end-to-end correctness but are slower.  If these fail but
# the unit tests above pass, the problem is in the data or I/O layer.
# ═══════════════════════════════════════════════════════════════════════════


class TestFetchDefinitionsIntegration:
    """Integration tests for ``fetch_definitions`` with real data."""

    def test_returns_definitions_index(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """GIVEN real component classes and the workbook
        WHEN ``fetch_definitions`` is called
        THEN it returns a ``DefinitionsIndex`` (not a bare dict or None).
        """
        assert isinstance(definitions_index, DefinitionsIndex)

    def test_by_signature_is_non_empty(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """The forward index should contain at least one entry if the
        workbook has any sheets matching the component classes.
        """
        assert (
            len(definitions_index.by_signature) > 0
        ), "by_signature should be populated from the workbook"

    def test_by_alias_is_non_empty(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """The reverse index should contain at least one entry."""
        assert len(definitions_index.by_alias) > 0, "by_alias should be populated from the workbook"

    def test_every_by_signature_value_is_alias_map(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """Every value in the forward index must be a ``Mapping`` whose
        keys are strings and values are tuples of strings.
        """
        for key, alias_map in definitions_index.by_signature.items():
            assert isinstance(
                alias_map, dict
            ), f"Expected dict for key {key}, got {type(alias_map)}"
            for canonical, aliases in alias_map.items():
                assert isinstance(
                    canonical, str
                ), f"Canonical key should be str, got {type(canonical)}"
                assert isinstance(aliases, tuple), f"Aliases should be tuple, got {type(aliases)}"

    def test_every_by_alias_value_is_component_attribute_info(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """Every value in the reverse index must be a
        ``ComponentAttributeInfo`` instance.
        """
        for key, info in definitions_index.by_alias.items():
            assert isinstance(
                info, ComponentAttributeInfo
            ), f"Expected ComponentAttributeInfo for key {key}, got {type(info)}"

    def test_forward_and_reverse_are_consistent(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """For every canonical name in the forward index, the reverse index
        should map that name back to a ``ComponentAttributeInfo`` that, when
        paired with the same class, is a valid forward key.

        This is a *cross-index invariant* — a powerful pattern for catching
        data integrity bugs.
        """
        for (cls, attr_info), alias_map in definitions_index.by_signature.items():
            for canonical in alias_map:
                reverse_result = definitions_index.by_alias.get((cls, canonical))
                assert reverse_result is not None, (
                    f"Canonical name '{canonical}' from forward index is missing "
                    f"in reverse index for class {cls.__name__}"
                )


class TestLookupHelpersIntegration:
    """Integration tests for the lookup helpers with real data."""

    def test_round_trip_signature_to_name_and_back(
        self,
        definitions_index: DefinitionsIndex,
    ) -> None:
        """Pick the first entry from the forward index and verify a
        round-trip: signature → canonical name → attribute info → same
        signature.

        This is a *round-trip test* — one of the most valuable integration
        test patterns because it validates two code paths at once.
        """
        # Arrange — grab the first entry
        first_key = next(iter(definitions_index.by_signature))
        cls, attr_info = first_key
        alias_map = definitions_index.by_signature[first_key]
        canonical = next(iter(alias_map))

        # Act — reverse lookup by name
        result = get_attribute_by_name(cls, canonical, definitions_index)

        # Assert — the result should carry the same signature
        assert result is not None, f"Reverse lookup failed for '{canonical}'"
        assert result.signature == attr_info.signature, (
            f"Round-trip signature mismatch for '{canonical}': "
            f"expected {attr_info.signature}, got {result.signature}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  EDGE-CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════
# Edge cases protect against regressions when the data or callers do
# something unexpected.
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Guard-rail tests for unusual or boundary inputs."""

    def test_fetch_with_no_matching_sheets_produces_empty_index(self) -> None:
        """GIVEN a ``classes`` dict whose type names match no sheets
        WHEN ``fetch_definitions`` is called
        THEN both indices are empty (no crash, no KeyError).
        """

        class _NoSheetClass:
            __name__ = "ZZZ_NoSuchSheet"
            __module__ = "test"

        classes = {_NoSheetClass: ComponentClassInfo(signature=(), fields={})}
        result = fetch_definitions(classes)
        assert isinstance(result, DefinitionsIndex)
        assert len(result.by_signature) == 0
        assert len(result.by_alias) == 0

    def test_empty_classes_dict_returns_empty_index(self) -> None:
        """GIVEN an empty ``classes`` dict
        WHEN ``fetch_definitions`` is called
        THEN both indices are empty.
        """
        result = fetch_definitions({})
        assert isinstance(result, DefinitionsIndex)
        assert len(result.by_signature) == 0
        assert len(result.by_alias) == 0

    def test_get_attribute_by_name_with_empty_string(
        self,
        synthetic_index: DefinitionsIndex,
    ) -> None:
        """Looking up an empty string should return ``None``, not crash."""
        result = get_attribute_by_name(_FakeDomain, "", synthetic_index)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
#  PERFORMANCE REGRESSION TEST
# ═══════════════════════════════════════════════════════════════════════════
# Keeping a performance guard in the test suite catches regressions early.
# This is intentionally generous — the goal is to catch O(n²) regressions,
# not micro-benchmark.
# ═══════════════════════════════════════════════════════════════════════════

# Based on the diagnostic history, the average time is ~30 ms.
# We set the threshold at 3× that to allow for CI variance.
_PERF_THRESHOLD_MS = 100.0
_PERF_SAMPLES = 10


class TestPerformance:
    """Lightweight performance regression guard."""

    def test_fetch_definitions_within_threshold(
        self,
        component_classes: dict[type, ComponentClassInfo],
    ) -> None:
        """GIVEN the real component classes
        WHEN ``fetch_definitions`` is timed over several samples
        THEN the average execution time stays within the threshold.

        If this test fails, a recent change likely introduced a performance
        regression.  Check the diagnostic history file for the baseline.
        """
        total = timeit(lambda: fetch_definitions(component_classes), number=_PERF_SAMPLES)
        avg_ms = (total / _PERF_SAMPLES) * 1000

        assert avg_ms < _PERF_THRESHOLD_MS, (
            f"fetch_definitions averaged {avg_ms:.1f} ms "
            f"(threshold: {_PERF_THRESHOLD_MS} ms over {_PERF_SAMPLES} samples)"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  DIRECT-RUN SUPPORT
# ═══════════════════════════════════════════════════════════════════════════
# Allows running this file directly with ``python definitions.py`` for a
# quick sanity check without requiring the pytest runner.
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
