from __future__ import annotations

from pprint import pprint

from components.data import Primitive
from components.definitions import _collect_module_classes
from humaniseT5.definitions import fetch_definitions

classes = _collect_module_classes("components.data", (Primitive,)) # dict[type, ComponentClassInfo]


print("\033c", end="")
definitions = fetch_definitions(classes)
pprint(definitions, width=120)
pprint(f"Final Output Structure: {list(definitions)}")