from __future__ import annotations

import dataclasses
import inspect
from importlib import import_module
from typing import Optional, get_type_hints

from humaniseT5.definitions.api import (
    ComponentClassInfo,
    fetch_definitions,
)


def _collect_module_classes(
    module_name: str,
    base_classes: tuple[str, ...],
) -> dict[type, ComponentClassInfo]:
    """Collect component classes defined in *module_name* that descend from
    *base_classes*.

    Returns an ordered mapping of class name → ``ComponentClassInfo`` carrying
    the class's flattened ``Signature`` and an insertion-ordered dict of
    ``{field_name: resolved_type}`` for every dataclass field.

    Base-class matching uses ``issubclass`` against lazily-imported classes
    to avoid the circular import between ``components.base`` and this module.
    """
    module = import_module(module_name)

    # Lazily resolve base class names to actual types so we can use
    # ``issubclass`` for reliable detection (the @component decorator
    # wraps classes in a slotted subclass, hiding the original bases).
    resolved_bases: list[type] = []
    base_module = import_module(name="components.base")
    for name in base_classes:
        cls = getattr(base_module, name, None)
        if cls is not None:
            resolved_bases.append(cls)

    result: dict[type, ComponentClassInfo] = {}

    for name, obj in vars(module).items():
        if not inspect.isclass(obj):
            continue
        if not any(issubclass(obj, base) for base in resolved_bases):
            continue
        # Skip the abstract bases themselves.
        if obj in resolved_bases:
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
            signature=obj.signature,
            fields=field_map,
        )

    return result


class Semantics:
    """Global Singleton for holding all definitions and licensed material. This is populated at runtime by fetching from the Excel sheets and can be accessed by any component or system that needs it. It is not intended to be modified after initial population, but is not strictly immutable."""

    __slots__ = ("language", "canonical_definitions", "_is_initialised")

    _is_initialised: bool
    _instance: Optional[Semantics] = None
    language: str

    def __new__(cls, language="en") -> Semantics:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "canonical_definitions", {})
        # object.__setattr__(self, "licensed_material", {})
        object.__setattr__(self, "_is_initialised", False)

        cls._instance = self
        return self

    def __init__(self, language="en") -> None:
        if self._is_initialised:
            return

        classes = _collect_module_classes(module_name="components.data", base_classes=("Primitive",))
        definitions = fetch_definitions(classes=classes, language=self.language)
        # licensed_material = fetch_licensed_material(classes, language=self.language)
        object.__setattr__(self, "canonical_definitions", definitions)
        # object.__setattr__(self, "licensed_material", licensed_material)
        object.__setattr__(self, "_is_initialised", True)


# Convenience global instance for easy access to definitions and licensed material.
SEMANTICS = Semantics(language="en")
