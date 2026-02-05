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


def _class_fields(cls: type) -> list[str] | None:
    result = []
    for f in dataclasses.fields(cls):
        # Only extract fields of type int
        if f.type == "int":
            field_info = f.name
            result.append(field_info)
    return result if result else None

def collect_module_classes(module) -> dict[str, list[str]]:
    """Collect classes defined in `module` and return mapping name -> fields.
    Only collect children of Primitive and only fields of type int.
    """
    result: dict[str, list[str]] = {}
    for name, obj in vars(module).items():
        if inspect.isclass(obj) and issubclass(obj, Primitive) and getattr(obj, "__module__", None) == module.__name__:
            # Skip if returned fields is empty (i.e. does not have any int fields)
            if not (fields := _class_fields(obj)):
                continue
            result[name] = fields
    return result


if __name__ == "__main__":
    print("\033c", end="")
    mod = import_module("components.data")
    classes = collect_module_classes(mod)

    pprint(classes, indent=2)