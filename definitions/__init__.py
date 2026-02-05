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

def _class_fields(cls: type) -> list[dict[str, str]]:
    result = []
    for f in dataclasses.fields(cls):
        field_info = {
            f.name: f.type,
        }
        result.append(field_info)
        
    return result

def collect_module_classes(module) -> dict[str, list[dict[str, str]]]:
    """Collect classes defined in `module` and return mapping name -> fields."""
    result: dict[str, list[dict[str, str]]] = {}
    for name, obj in vars(module).items():
        if inspect.isclass(obj) and getattr(obj, "__module__", None) == module.__name__:
            result[name] = _class_fields(obj)
    return result


if __name__ == "__main__":
    mod = import_module("components.data")
    classes = collect_module_classes(mod)

    print("\033c", end="")
    pprint(classes, indent=2)

    extracted_example = { 'CharacteristicCode': [ {'upp_position': 'int'},
                        {'subtype': 'int'},
                        {'category': 'int'}],}

    pprint(extracted_example, indent=2)