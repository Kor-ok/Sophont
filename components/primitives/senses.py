#region Setup
from __future__ import annotations

import sys
from enum import Enum, auto
from pathlib import Path

import pandas as pd

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent.parent.parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from components.primitives.init_mappings import (  # noqa: E402
    LANG_CODE,
    XLSX_PATH,
)

SHEET_NAMES = ["vision", "hearing", "smell", "touch", "perception", "awareness"]
tables = {}
for sheet in SHEET_NAMES:
    data_df = pd.read_excel(
        XLSX_PATH, sheet_name=sheet+f".senses.{LANG_CODE}", engine="openpyxl", header=0
    )
    tables[sheet] = data_df.to_dict(orient="records")
#endregion

class SenseType(Enum):
    VISION = (auto(), 3)
    HEARING = (auto(), 4)
    SMELL = (auto(), 1)
    TOUCH = (auto(), 1)
    PERCEPTION = (auto(), 2)
    AWARENESS = (auto(), 1)

    def __init__(self, rank: int, max_bands: int):
        self._value_ = rank
        self.max_bands = max_bands
        self.table = tables[self.name.lower()]


class Sense:
    # constant: NamedTuple # When used by Sensor it is regarded as Sensation, when used by Emitter it is regarded as Emission
    def __init__(self, sense_type: SenseType, band_values: tuple[int, ...] | None = None, constant_values: tuple[int, ...] | None = None):
        self.sense_type: SenseType = sense_type
        self.bands: tuple[int, ...] = ()
        self.constants: tuple[int, ...] = ()
        self._initialise_defaults(band_values, constant_values)

    def _initialise_defaults(self, band_values: tuple[int, ...] | None = None, constant_values: tuple[int, ...] | None = None):
        n = self.sense_type.max_bands
        if band_values is not None and len(band_values) != n:
            print(f"band_values must have length {n} for sense type {self.sense_type.name}")
            # use the provided values up to n, and fill the rest with -99
            self.bands = band_values[:n] + (-99,) * (n - len(band_values))
        elif band_values is None:
            self.bands = (-99,) * n
        else:
            self.bands = band_values
        if constant_values is not None and len(constant_values) != n:
            print(f"constant_values must have length {n} for sense type {self.sense_type.name}")
            # use the provided values up to n, and fill the rest with -99
            self.constants = constant_values[:n] + (-99,) * (n - len(constant_values))
        elif constant_values is None:
            self.constants = (-99,) * n
        else:
            self.constants = constant_values

    def _get_sense_data_by_code(self, code: int, sense: SenseType, header: str):
        # code is the row number in the table (0-based and skipping header)
        # return early if header not in table
        if header not in sense.table[0]:
            raise ValueError(f"Header '{header}' not found in sense table for {sense.name}")
        if code < 1 or code > len(sense.table):
            return "Undefined"
        return sense.table[code-1].get(header)
    
    def get_band_data(self, header: str) -> tuple[str, ...]:
        names = []
        for band_value in self.bands:
            i = band_value
            name = self._get_sense_data_by_code(i, self.sense_type, header)
            names.append(name)
        return tuple(names)

class Sensor:
    sensations: set[Sense]

class Emitter:
    emissions: set[Sense]


def demo_sense():
    vision_sense_example = Sense(SenseType.VISION, band_values=(9, 8, 7), constant_values=(16, 16, 16))
    print(vision_sense_example.get_band_data("Name"))

if __name__ == "__main__":
    print("\033c", end="")
    demo_sense()
