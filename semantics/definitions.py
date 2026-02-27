from __future__ import annotations

from typing import Any, Optional

from api.t5 import (
    build_definitions_indices,
    get_semantics_from_instance,
)
from components.base import Primitive
from components.primitives import MODULE_GRAPH

classes = MODULE_GRAPH.subclasses_of(Primitive)


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

        # classes = MODULE_GRAPH.subclasses_of(Primitive)
        definitions = build_definitions_indices(classes=classes, language=self.language)
        # licensed_material = fetch_licensed_material(classes, language=self.language)
        object.__setattr__(self, "canonical_definitions", definitions)
        # object.__setattr__(self, "licensed_material", licensed_material)
        object.__setattr__(self, "_is_initialised", True)

    def __setattr__(self, key, value):
        raise AttributeError("Semantics is immutable and cannot be modified after initialisation.")

    def of(self, instance: Any) -> dict[type, dict[str, Any]]:
        """Helper method to get the semantics of a component instance using the by_signature index."""
        return get_semantics_from_instance(instance, self.canonical_definitions, classes)


# Convenience global instance for easy access to definitions and licensed material.
SEMANTICS = Semantics(language="en")
