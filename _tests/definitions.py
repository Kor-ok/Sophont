from __future__ import annotations

import sys
from datetime import datetime as dt
from pathlib import Path
from timeit import timeit

from colorama import Fore
from numpy import int8

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.data import (
    CharacteristicCode,
    GenderCode,
    KnowledgeCode,
    SkillCode,
)
from components.definitions import DEFINITIONS
from humaniseT5.definitions.api import get_alias_map_by_signature, get_attribute_by_name

DIAGNOSTIC_HISTORY_FILE = Path(__file__).parent / f"{Path(__file__).stem}_diagnostic_history.txt"

# ---------------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------------
# Clear Terminal
print("\033c", end="")

# ── Test forward lookup (component → aliases) ────────────────────────
print("\n── Forward lookup (component → aliases) ──")
test_components = [
    test_skillcode := SkillCode(key=int8(25), set=int8(1), group=int8(-99)),
    test_knowledgecode := KnowledgeCode(
        key=int8(41),
        focus=int8(-99),
        associated_skill=SkillCode(key=int8(25), set=int8(1), group=int8(-99)),
    ),
    test_characteristiccode := CharacteristicCode(
        upp_position=int8(2), subtype=int8(1), category=int8(1)
    ),
    test_gendercode := GenderCode(key=int8(5)),
]

for component in test_components:
    print(f"Semantics for {component.__class__.__name__}: {component.semantics}")

# ── Test direct reverse lookup (aliases → component) ────────────────────────
print("\n── Direct Reverse lookup (aliases → component) ──")
test_cases = [
    (SkillCode, "communications"),
    (KnowledgeCode, "grav"),
    (CharacteristicCode, "gra"),
    (GenderCode, "4"),
]

for cls, alias in test_cases:
    value = get_attribute_by_name(cls, alias, DEFINITIONS.canonical_definitions)
    if value is None:
        print(Fore.RED + f"Lookup by name for {cls.__name__} with name '{alias}': Not found" + Fore.RESET)
    else:
        print(f"Lookup by name for {cls.__name__} with name '{alias}': {value}")

# ── Test create component via alias ────────────────────────
print("\n── Create component via alias ──")
test_cases_raw_creation = [
    test_skillcode := SkillCode(key=int8(25), set=int8(1), group=int8(-99)),
    test_knowledgecode := KnowledgeCode(
        key=int8(41),
        focus=int8(-99),
        associated_skill=SkillCode(key=int8(25), set=int8(1), group=int8(-99)),
    ),
    test_characteristiccode := CharacteristicCode(
        upp_position=int8(2), subtype=int8(1), category=int8(1)
    ),
    test_gendercode := GenderCode(key=int8(5)),
]
test_cases_by_name = [
    SkillCode.by_name(name="communications"),
    KnowledgeCode.by_name(name="grav"),
    CharacteristicCode.by_name(name="gra"),
    GenderCode.by_name(name="4"),
]
for raw, by_name in zip(test_cases_raw_creation, test_cases_by_name):
    if raw == by_name:
        print(f"Factory method by_name for {raw.__class__.__name__} returned the expected instance.")
    else:
        print(Fore.RED + f"Factory method by_name for {raw.__class__.__name__} did not return the expected instance." + Fore.RESET)

# ── Test create component via alias ────────────────────────
example_knowledge_code_raw = KnowledgeCode(
        key=int8(41),
        focus=int8(-99),
        associated_skill=SkillCode(key=int8(25), set=int8(1), group=int8(-99)),
    ) # "grav"


inspection_values = [
    ("Semantic: ", example_knowledge_code_raw.semantics),
    ("Signature: ", example_knowledge_code_raw.signature), # type: ignore[attr-defined]
    ("As Tuple: ", example_knowledge_code_raw._as_tuple()), # type: ignore[attr-defined]
    ("Cache Key: ", example_knowledge_code_raw._cache_key()), # type: ignore[attr-defined]
]

print("\n── Create component raw ──")
for description, value in inspection_values:
    print(description, value)

print("\n── Create component by name ──")
example_knowledge_code_by_name = KnowledgeCode.by_name("grav")

inspection_values = [
    ("Semantic: ", example_knowledge_code_by_name.semantics),
    ("Signature: ", example_knowledge_code_by_name.signature), # type: ignore[attr-defined]
    ("As Tuple: ", example_knowledge_code_by_name._as_tuple()), # type: ignore[attr-defined]
    ("Cache Key: ", example_knowledge_code_by_name._cache_key()), # type: ignore[attr-defined]
]
for description, value in inspection_values:
    print(description, value)

print("\n── Instance Equality Check ──")
try:
    assert example_knowledge_code_raw == example_knowledge_code_by_name
    print(Fore.GREEN + "Instances match for raw and by-name instances." + Fore.RESET)
except AssertionError:
    print(Fore.RED + "Instances do NOT match for raw and by-name instances." + Fore.RESET)

# ---------------------------------------------------------------------------
# PERFORMANCE BENCHMARKS
# ---------------------------------------------------------------------------
print("\n── Performance benchmarks ──")
iterations = 100
benchmark_cases = [
    ("Forward lookup for SkillCode with signature (25, 1, -99)", lambda: get_alias_map_by_signature(
        cls=SkillCode,
        sig=(int8(25), int8(1), int8(-99)),
        search_index=DEFINITIONS.canonical_definitions,
    )),
    ("Reverse lookup for SkillCode with name 'communications'", lambda: get_attribute_by_name(
        cls=SkillCode,
        name="communications",
        search_index=DEFINITIONS.canonical_definitions,
    )),
]
results = []
for description, func in benchmark_cases:
    time_taken = timeit(func, number=iterations)
    result = (f"{description}: {(time_taken/iterations * 1000000):.6f} microseconds averaged over {iterations} iterations")
    results.append(result)
print("\n".join(results))


# ---------------------------------------------------------------------------
# OUTPUT DIAGNOSTIC HISTORY TO FILE
# ---------------------------------------------------------------------------
# with open(DIAGNOSTIC_HISTORY_FILE, "a") as f:
#     was_write_success = f.write(f"{dt.now()}: Benchmarks: {', '.join(results)}\n")
#     if was_write_success:
#         print(f"Diagnostic history saved to: {DIAGNOSTIC_HISTORY_FILE}")
#     else:
#         print("Failed to write diagnostic history.")