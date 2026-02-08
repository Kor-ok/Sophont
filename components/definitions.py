from __future__ import annotations

import dataclasses
import inspect
from importlib import import_module
from typing import NamedTuple, Optional, get_type_hints

from components.data import Primitive
from humaniseT5.definitions import (
    fetch_definitions,
    fetch_licensed_material,
)


class ComponentClassInfo(NamedTuple):
    """Collected metadata for a single component class."""

    signature: tuple[type, ...]
    """Flattened primitive-type tuple (from the class's ``Signature`` ClassVar)."""
    fields: dict[str, type]
    """Insertion-ordered mapping of field name → resolved type."""


def _collect_module_classes(
    module_name: str,
    base_classes: tuple[type, ...],
) -> dict[type, ComponentClassInfo]:
    """Collect component classes defined in *module_name* that descend from
    *base_classes*.

    Returns an ordered mapping of class name → ``ComponentClassInfo`` carrying
    the class's flattened ``Signature`` and an insertion-ordered dict of
    ``{field_name: resolved_type}`` for every dataclass field.
    """
    module = import_module(module_name)
    result: dict[type, ComponentClassInfo] = {}

    for name, obj in vars(module).items():
        if not inspect.isclass(obj):
            continue
        if not issubclass(obj, base_classes):
            continue
        if getattr(obj, "__module__", None) != module_name:
            continue

        try:
            cls_fields = dataclasses.fields(obj)
        except TypeError:
            continue
        if not cls_fields:
            continue

        # Resolve string annotations (from ``from __future__ import annotations``)
        # to actual types so callers receive real type objects.
        hints = get_type_hints(obj)

        field_map: dict[str, type] = {}
        for f in cls_fields:
            field_map[f.name] = hints.get(f.name, f.type)

        result[obj] = ComponentClassInfo(
            signature=getattr(obj, "Signature", ()),
            fields=field_map,
        )

    return result


class Definitions:
    """Global Singleton for holding all definitions and licensed material. This is populated at runtime by fetching from the Excel sheets and can be accessed by any component or system that needs it. It is not intended to be modified after initial population, but is not strictly immutable."""

    __slots__ = ("language", "canonical_definitions", "licensed_material", "_is_initialised")

    _is_initialised: bool
    _instance: Optional[Definitions] = None
    language: str

    def __new__(cls, language="en") -> Definitions:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "canonical_definitions", {})
        object.__setattr__(self, "licensed_material", {})
        object.__setattr__(self, "_is_initialised", False)

        cls._instance = self
        return self

    def __init__(self, language="en") -> None:
        if self._is_initialised:
            return
        classes = _collect_module_classes("components.data", (Primitive,))
        definitions = fetch_definitions(classes, language=self.language)
        licensed_material = fetch_licensed_material(classes, language=self.language)
        object.__setattr__(self, "canonical_definitions", definitions)
        object.__setattr__(self, "licensed_material", licensed_material)
        object.__setattr__(self, "_is_initialised", True)


# Convenience global instance for easy access to definitions and licensed material.
DEFINITIONS = Definitions(language="en")
