from __future__ import annotations

import dataclasses
import inspect
import sys
from importlib import import_module
from pathlib import Path
from pprint import pprint

_src_path = Path(__file__).parent.parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from components.data import Primitive  # noqa: E402
from humaniseT5.definitions import (  # noqa: E402
    fetch_definitions,
    fetch_licensed_material,
)


def collect_module_classes(
    module_name: str,
    base_classes: tuple[type, ...],
    field_types: tuple[object, ...],
) -> dict[str, list[str]]:
    """Collect classes defined in `module_name` and return mapping name -> fields.
    Only collect children of base classes and only fields of specified types.
    """
    module = import_module(module_name)
    type_names = {
        ft if isinstance(ft, str) else getattr(ft, "__name__", str(ft))
        for ft in field_types
    }
    result: dict[str, list[str]] = {}
    for name, obj in vars(module).items():
        if not inspect.isclass(obj):
            continue
        if not issubclass(obj, base_classes):
            continue
        if getattr(obj, "__module__", None) != module_name:
            continue
        fields = [
            f.name
            for f in dataclasses.fields(obj)
            if f.type in field_types
            or getattr(f.type, "__name__", None) in type_names
            or (isinstance(f.type, str) and f.type in type_names)
        ]
        if not fields:
            continue
        result[name] = fields
    return result

def demo_definitions():
    print("\033c", end="")
    classes = collect_module_classes("components.data", (Primitive,), ("int",))
    definitions = fetch_definitions(classes, language="en")
    pprint(definitions, indent=2)

def demo_licensed_material():
    print("\033c", end="")
    classes = collect_module_classes("components.data", (Primitive,), ("int",))
    licensed_material = fetch_licensed_material(classes, language="en")
    pprint(licensed_material, indent=2)

if __name__ == "__main__":
    print("\033c", end="")
    demo_licensed_material()