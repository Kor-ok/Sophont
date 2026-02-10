from __future__ import annotations

import sys
from datetime import datetime as dt
from pathlib import Path
from timeit import timeit

from pympler import asizeof

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from components.definitions import (
    _collect_module_classes,
)
from humaniseT5.definitions.api import fetch_definitions

DIAGNOSTIC_HISTORY_FILE = Path(__file__).parent / f"{Path(__file__).stem}_diagnostic_history.txt"

# ---------------------------------------------------------------------------
# Timing / diagnostics
# ---------------------------------------------------------------------------
# Clear Terminal
print("\033c", end="")


classes = _collect_module_classes("components.data", ("Primitive",))
function = fetch_definitions
samples = 100
fetch_definitions_total_time = timeit(lambda: function(classes), number=samples)
fetch_definitions_time = fetch_definitions_total_time / samples * 1000
print(f"{function.__name__} average execution time({samples} samples): {fetch_definitions_time:.2f} ms")
definitions = function(classes)
print(f"asizeof.asizeof(definitions): {asizeof.asizeof(definitions) / 1024:.2f} kb")


with open(DIAGNOSTIC_HISTORY_FILE, "a") as f:
    was_write_success = f.write(f"{dt.now()}: fetch_definitions_time={fetch_definitions_time:.2f} ms, size={asizeof.asizeof(definitions) / 1024:.2f} kb\n")
    if was_write_success:
        print(f"Diagnostic history saved to: {DIAGNOSTIC_HISTORY_FILE}")
    else:
        print("Failed to write diagnostic history.")