"""Prototype: Semantic Map -> Component Signature generation.

Compares two paradigms:
  1. OOP  — pre-parsed immutable SemanticMap; hot-path signature generation.
  2. Algo — single-pass recursive traversal, zero intermediate structures.
"""

from __future__ import annotations

import struct
from timeit import timeit
from typing import Any, NamedTuple, Optional

from colorama import Fore, Style
from colorama import init as colorama_init

from utils.terminal import divider, header

colorama_init(autoreset=True, convert=True)


# ═══════════════════════════════════════════════════════════════════════════════
# OOP Paradigm
# ═══════════════════════════════════════════════════════════════════════════════


class SemanticMapElement(NamedTuple):
    """Immutable flyweight: one flattened node of the semantic map."""

    depth: int
    domain_identity: int
    pre_nested_count: int


class SemanticMap:
    """Pre-parsed semantic map — parse once, reuse for many signature generations.

    Analogous to a *Component type definition* in ECS terms.
    Follows the flyweight / immutable-item pattern used elsewhere in the repo.
    """

    __slots__ = ("elements",)

    def __new__(cls, elements: tuple[SemanticMapElement, ...]) -> SemanticMap:
        instance = super().__new__(cls)
        instance.elements = elements
        return instance

    def __init__(self, elements: tuple[SemanticMapElement, ...]) -> None:
        pass

    # -- factory ----------------------------------------------------------

    @staticmethod
    def from_raw(raw: tuple[Any, ...]) -> SemanticMap:
        """Build a SemanticMap from a nested raw-tuple descriptor."""
        return SemanticMap(elements=tuple(SemanticMap._parse(raw, 0)))

    @staticmethod
    def _parse(
        raw: tuple[Any, ...],
        depth: int,
    ) -> list[SemanticMapElement]:
        """Recursively flatten *raw* into an ordered list of elements.

        Cleaner iteration compared to the original while-loop:
        • Identifies domain_identity once at position 0.
        • Dispatches remaining items by type in a single pass.
        """
        if not raw:
            return []
        result: list[SemanticMapElement] = []
        first = raw[0]
        domain_id: Optional[int] = first if not isinstance(first, tuple) else None
        start = 1 if domain_id is not None else 0
        for i in range(start, len(raw)):
            val = raw[i]
            if isinstance(val, tuple):
                result.extend(SemanticMap._parse(val, depth + 1))
            elif domain_id is not None:
                result.append(SemanticMapElement(depth, domain_id, val))
        return result


def generate_signature_oop(
    semantic_map: SemanticMap,
    semantic_signature: tuple[int, ...],
) -> bytes:
    """Hot-path OOP signature generation from a pre-parsed map.

    Optimisations over the original:
    • **No debug logging / I/O** in the hot path — this alone removed ~95 %
      of the per-call cost when the logger was active (f-string evaluation +
      ``logger.debug`` call overhead even at non-DEBUG levels).
    • Uses ``struct.pack`` for a single C-level int→bytes conversion instead of
      building an intermediate ``array('b', ...)`` then calling ``.tobytes()``.
    • Iterates via NamedTuple unpacking — one tuple unpack per element replaces
      three attribute lookups (``element.depth``, ``.domain_identity``,
      ``.pre_nested_count``).
    """
    result: list[int] = []
    seen: set[tuple[int, int]] = set()
    sig_idx = 0
    for depth, domain_id, count in semantic_map.elements:
        key = (depth, domain_id)
        if key not in seen:
            seen.add(key)
            result.append(domain_id)
        end = sig_idx + count
        result.extend(semantic_signature[sig_idx:end])
        sig_idx = end
    return struct.pack(f"{len(result)}b", *result)


# ═══════════════════════════════════════════════════════════════════════════════
# Algorithmic Paradigm
# ═══════════════════════════════════════════════════════════════════════════════


def generate_signature_algorithmic(
    raw: tuple[Any, ...],
    semantic_signature: tuple[int, ...],
) -> bytes:
    """Single-pass signature generation — no intermediate parse objects.

    Walks the nested raw-tuple map and assembles the component signature in one
    recursive traversal, fusing the parse and generate steps.

    Optimisations over the original ``generate_component_signature_via_itertools``:
    • **Fused parse + generate** — eliminates an entire intermediate list of
      ``(depth, domain_id, count)`` tuples.
    • Uses ``nonlocal`` instead of a mutable-list-as-int workaround.
    • Removes the (unused) ``itertools.chain`` import.
    • Removes the redundant ``elif isinstance(element_value, tuple)`` branch
      (already handled by the preceding ``if``).
    • Uses ``struct.pack`` for direct int→bytes conversion.
    """
    result: list[int] = []
    seen: set[tuple[int, int]] = set()
    sig_idx = 0

    def _walk(node: tuple[Any, ...], depth: int) -> None:
        nonlocal sig_idx
        if not node:
            return
        first = node[0]
        domain_id: Optional[int] = first if not isinstance(first, tuple) else None
        start = 1 if domain_id is not None else 0
        for i in range(start, len(node)):
            val = node[i]
            if isinstance(val, tuple):
                _walk(val, depth + 1)
            elif domain_id is not None:
                key = (depth, domain_id)
                if key not in seen:
                    seen.add(key)
                    result.append(domain_id)
                end = sig_idx + val
                result.extend(semantic_signature[sig_idx:end])
                sig_idx = end

    _walk(raw, 0)
    return struct.pack(f"{len(result)}b", *result)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _expected_bytes(expected: tuple[int, ...]) -> bytes:
    """Convert an expected-result tuple of signed ints to bytes."""
    return struct.pack(f"{len(expected)}b", *expected)


def _bytes_to_ints(data: bytes) -> tuple[int, ...]:
    """Unpack bytes back to a tuple of signed ints (for display)."""
    return struct.unpack(f"{len(data)}b", data)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Harness
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    header("Prototype — Semantic Signature → Component Signature")

    test_vectors = {
        "characteristic": [
            (raw := (0, 3)),
            (sig := (1, 0, 1)),
            (exp := (0, 1, 0, 1)),
        ],
        "knowledge": [
            (raw := (2, 2, (1, 3))),
            (sig := (15, -99, 59, 5, 1)),
            (exp := (2, 15, -99, 1, 59, 5, 1)),
        ],
        "complex": [
            (raw := (4, 1, (0, 3), 2, ((2, 2, (1, 3))), 1)),
            (sig := (6, 1, 0, 1, 4, 3, 41, -99, 21, 1, -99, 1)),
            (exp := (4, 6, 0, 1, 0, 1, 4, 3, 2, 41, -99, 1, 21, 1, -99, 1)),
        ],
    }

    # Pre-parse maps for OOP paradigm (done once; reused in hot-path benchmarks)
    parsed_maps = {key: SemanticMap.from_raw(r) for key, (r, _, _) in test_vectors.items()}

    divider()
    print()

    # ── Correctness ───────────────────────────────────────────────────────────
    all_pass = True
    for key, (raw, sig, exp) in test_vectors.items():
        exp_b = _expected_bytes(exp)
        sm = parsed_maps[key]

        oop_out = generate_signature_oop(sm, sig)
        alg_out = generate_signature_algorithmic(raw, sig)

        oop_ok = oop_out == exp_b
        alg_ok = alg_out == exp_b
        all_pass &= oop_ok and alg_ok

        oop_tag = f"{Fore.GREEN}PASS" if oop_ok else f"{Fore.RED}FAIL"
        alg_tag = f"{Fore.GREEN}PASS" if alg_ok else f"{Fore.RED}FAIL"

        print(f"{Fore.WHITE}{key}{Style.RESET_ALL}")
        print(f"  signature : {Fore.BLUE}{sig}{Style.RESET_ALL}")
        print(f"  expected  : {exp}")
        print(f"  OOP  → {_bytes_to_ints(oop_out)}  [{oop_tag}{Style.RESET_ALL}]")
        print(f"  Algo → {_bytes_to_ints(alg_out)}  [{alg_tag}{Style.RESET_ALL}]")
        print()

    if not all_pass:
        print(f"{Fore.RED}Some tests FAILED — skipping benchmarks.{Style.RESET_ALL}")
        raise SystemExit(1)

    # ── Benchmarks ────────────────────────────────────────────────────────────
    N = 10_000
    header(f"Benchmarks ({N:,} iterations each)")

    cold_times: list[float] = []
    hot_times: list[float] = []
    alg_times: list[float] = []

    for key, (raw, sig, _) in test_vectors.items():
        sm = parsed_maps[key]

        # OOP cold path: parse + generate (full round-trip)
        cold_t = timeit(
            lambda _r=raw, _s=sig: generate_signature_oop(SemanticMap.from_raw(_r), _s),
            number=N,
        )
        # OOP hot path: generate only (pre-parsed map, the real use-case)
        hot_t = timeit(
            lambda _m=sm, _s=sig: generate_signature_oop(_m, _s),
            number=N,
        )
        # Algorithmic: single-pass parse + generate
        alg_t = timeit(
            lambda _r=raw, _s=sig: generate_signature_algorithmic(_r, _s),
            number=N,
        )

        cold_times.append(cold_t)
        hot_times.append(hot_t)
        alg_times.append(alg_t)

        print(f"{Fore.WHITE}{key}{Style.RESET_ALL}")
        print(
            f"  OOP  cold (parse+gen) : "
            f"{Fore.BLUE}{cold_t * 1000 / N:.4f} ms/call{Style.RESET_ALL}"
        )
        print(
            f"  OOP  hot  (gen only)  : "
            f"{Fore.GREEN}{hot_t * 1000 / N:.4f} ms/call{Style.RESET_ALL}"
        )
        print(
            f"  Algorithmic           : "
            f"{Fore.CYAN}{alg_t * 1000 / N:.4f} ms/call{Style.RESET_ALL}"
        )
        fastest = min(cold_t, hot_t, alg_t)
        if fastest == hot_t:
            label = f"{Fore.GREEN}OOP hot-path"
        elif fastest == cold_t:
            label = f"{Fore.BLUE}OOP cold-path"
        else:
            label = f"{Fore.CYAN}Algorithmic"
        print(f"  Winner: {label}{Style.RESET_ALL}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    header("Summary (averages)")

    avg_cold = sum(cold_times) / len(cold_times) * 1000 / N
    avg_hot = sum(hot_times) / len(hot_times) * 1000 / N
    avg_alg = sum(alg_times) / len(alg_times) * 1000 / N

    # Baselines from the original implementation (1000 iterations)
    ORIGINAL_OOP_MS = 0.054843  # parse + generate + debug logging
    ORIGINAL_ALG_MS = 0.002764  # itertools variant

    print(f"  {Fore.BLUE}OOP  cold  : {avg_cold:.4f} ms/call{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}OOP  hot   : {avg_hot:.4f} ms/call{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}Algorithmic: {avg_alg:.4f} ms/call{Style.RESET_ALL}")
    print()

    cold_speedup = ORIGINAL_OOP_MS / avg_cold if avg_cold else float("inf")
    hot_speedup = ORIGINAL_OOP_MS / avg_hot if avg_hot else float("inf")
    alg_speedup = ORIGINAL_ALG_MS / avg_alg if avg_alg else float("inf")

    print(f"  Speedup vs original OOP  (cold): {Fore.BLUE}{cold_speedup:.1f}x{Style.RESET_ALL}")
    print(f"  Speedup vs original OOP  (hot) : {Fore.GREEN}{hot_speedup:.1f}x{Style.RESET_ALL}")
    print(f"  Speedup vs original Algo       : {Fore.CYAN}{alg_speedup:.1f}x{Style.RESET_ALL}")
    print()

    overall = min(avg_cold, avg_hot, avg_alg)
    if overall == avg_hot:
        print(f"  {Fore.GREEN}Overall winner: OOP hot-path{Style.RESET_ALL}")
    elif overall == avg_cold:
        print(f"  {Fore.BLUE}Overall winner: OOP cold-path{Style.RESET_ALL}")
    else:
        print(f"  {Fore.CYAN}Overall winner: Algorithmic{Style.RESET_ALL}")
