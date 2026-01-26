from __future__ import annotations

import os
import sys

# Get the absolute path to the "src" directory
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")

# Add it to sys.path if not already present
if src_path not in sys.path:
    sys.path.append(src_path)

from t5humanise.distances.range import _range_band_width_meters  # type: ignore # noqa: E402

value = _range_band_width_meters(5)
print(value)