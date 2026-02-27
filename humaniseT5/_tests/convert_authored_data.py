from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, get_args

import pandas as pd
import pytest
from colorama import Fore, Style
from colorama import init as colorama_init

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


from humaniseT5.utils import Converters, ConvertersType, NestedIntTuple

colorama_init(autoreset=True)

# ---------------------------------------------------------------------------
# Lightweight synthetic fixtures — used by *unit* tests that must not depend
# on the real workbook.  This keeps those tests fast, deterministic, and easy
# to reason about.
# ---------------------------------------------------------------------------

SOURCE_NAME = "fake_authored_data_cases"
FAKE_DATA_SOURCE = Path(__file__).parent / f"{SOURCE_NAME}.xlsx"

@pytest.fixture(scope="session")
def fake_authored_data_cases() -> dict[str, Any]:
    """Load a small synthetic dataset of authored data cases from an Excel file.

    This allows us to test the conversion logic on a variety of realistic
    inputs without depending on the real workbook, which keeps these tests
    fast and deterministic.
    """
    df = pd.read_excel(FAKE_DATA_SOURCE)

    result = {}

    for _, row in df.iterrows():
        case_name = row[SOURCE_NAME]
        input_value = row["value"]

        result[case_name] = input_value

    return result

# ═══════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
COLOUR_CODING = {
    int: Fore.GREEN,
    list[int]: Fore.LIGHTGREEN_EX,
    tuple[int, ...]: Fore.CYAN,
    NestedIntTuple: Fore.LIGHTCYAN_EX,
    str: Fore.YELLOW,
    list[str]: Fore.LIGHTYELLOW_EX,
    bool: Fore.MAGENTA,
    }

def values_aligner(keys: list[str], padding: int = 0) -> int:
     """Helper to get the max of line lengths from the list of keys"""
     return max(len(key) for key in keys) + padding

def _type_parser(input_value: Any) -> tuple[str, str]:
    """Helper function to format the type of an input value for display in test output."""
    type_args = get_args(input_value.__orig_class__) if hasattr(input_value, "__orig_class__") else type(input_value)
    # If an element from the type tuple appears in our colour coding, use the corresponding colour; otherwise, default to white.
    for type_arg in (type_args if isinstance(type_args, tuple) else (type_args,)):
        colour = COLOUR_CODING.get(type_arg, Fore.WHITE)
        break
    return f"{Fore.RESET}{input_value.value}", f"{colour}{type_args}{Style.RESET_ALL}"

converters: ConvertersType = {
    "single int": Converters.to_python_int,
    "comma delimited int list": Converters.list_int,
    "simple string": Converters.to_str,
    "comma delimited string list": Converters.list_str,
    "tuple[int, …]": Converters.tuple_int,
    "nested tuple[Any, …]": Converters.tuple_int,
    "bool true": Converters.to_python_bool,
    "bool false": Converters.to_python_bool,
    # "empty": None,
    # "code text": None,
}

columns = converters.keys()

# ═══════════════════════════════════════════════════════════════════════════
#  DEBUG DISPLAY
# ═══════════════════════════════════════════════════════════════════════════

def debug_display() -> None:

    result = {}
    df = pd.read_excel(FAKE_DATA_SOURCE, engine="openpyxl", converters=converters) # dtype=dtypes
    # Case Names are headers; Input Values are the first row of data
    for column in columns:
        case_name = column
        input_value = df[column].iloc[0]
        result[case_name] = input_value

    def test_fake_authored_data_cases() -> None:
        alignment_padding = values_aligner(list(result.keys()))
        for case_name, input_value in result.items():
            type_str, type_coloured = _type_parser(input_value)
            print(f"{Fore.CYAN}{case_name}: {(' ' * (alignment_padding - len(case_name)))}{type_str} {type_coloured}{Style.RESET_ALL}")

    def test_converted_values() -> None:
        for case_name, input_value in result.items():
            keys_alignment_padding = values_aligner(list(result.keys()))
            value_str, type_str = _type_parser(input_value)
            print(f"{Fore.YELLOW}{case_name}: {(' ' * (keys_alignment_padding - len(case_name)))}{value_str} {type_str}{Style.RESET_ALL}")

    # test_fake_authored_data_cases()
    # print()
    test_converted_values()

# ═══════════════════════════════════════════════════════════════════════════
#  UNIT TESTS — pure logic, no I/O
# ═══════════════════════════════════════════════════════════════════════════
# These test individual helper functions using the synthetic fixture.
# They are fast and deterministic — if they fail, the bug is in the
# function's logic, not in the data.
# ═══════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    debug_display()
    print()
    # raise SystemExit(pytest.main([__file__, "-v"]))