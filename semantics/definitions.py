from __future__ import annotations

from typing import Any, Optional

from rich import print
from rich.pretty import pprint

from api.t5 import (
    build_definitions_indices,
    get_primitive_semantics_from_instance,
)
from components.applied import MODULE_GRAPH as APPLIED_MODULE_GRAPH
from components.base import Applied, Primitive
from components.primitives import MODULE_GRAPH as PRIMITIVES_MODULE_GRAPH
from utils.semantics import convert_bytes_to_tuple

primitives_subclasses = PRIMITIVES_MODULE_GRAPH.subclasses_of(Primitive)
# pprint(primitives_subclasses)
applied_subclasses = APPLIED_MODULE_GRAPH.subclasses_of(Applied)
# pprint(applied_subclasses)


class Semantics:
    """Global Singleton  for holding  all  definitions and licensed material.
    This is populated at runtime by fetching from the Excel sheets and can
    be  accessed by any component  or system  that  needs it.   It  is not
    intended to be modified after  initial population, but is not strictly
    immutable."""

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
        object.__setattr__(self, "_is_initialised", False)

        cls._instance = self
        return self

    def __init__(self, language="en") -> None:
        if self._is_initialised:
            return

        object.__setattr__(
            self,
            "canonical_definitions",
            build_definitions_indices(classes=primitives_subclasses, language=self.language),
        )
        object.__setattr__(self, "_is_initialised", True)

    def __setattr__(self, key, value):
        raise AttributeError("Semantics is immutable and cannot be modified after initialisation.")

    def of(self, instance: Any) -> dict[type, dict[tuple[int, str] | str, Any]]:  # SemanticInfo
        """Helper method to get the semantics of a component instance using the
        by_signature index via the T5 API."""

        if isinstance(instance, Primitive):
            return get_primitive_semantics_from_instance(
                instance, self.canonical_definitions, primitives_subclasses
            )
        elif isinstance(instance, Applied):
            return get_primitive_semantics_from_instance(
                instance, self.canonical_definitions, applied_subclasses
            )
        else:
            raise TypeError("Instance must be a Primitive or Applied component.")

    def create(self, type: type, name: str, **kwargs) -> Any:
        """Helper method to create a component instance from a canonical name and
        keyword arguments, using the by_alias_for_signature index via the T5 API."""
        search_domain: int = type.subclass_dict[type]
        # Do a fuzzy search for the string name as the names are command-separated aliases.
        for domain, aliases in self.canonical_definitions.by_alias_for_signature:
            if name.lower() in (alias.lower() for alias in aliases.split(",")):
                try:
                    search = self.canonical_definitions.by_alias_for_signature[
                        (search_domain, aliases)
                    ]
                    tuple_result = convert_bytes_to_tuple(search)[1:]
                    instance = type(*tuple_result)
                    return instance
                except KeyError:
                    print(
                        f"[bold red]Error:[/bold red] No component found for type {type.__name__} with name '{name}' in domain {search_domain}."
                    )
                    continue


# Convenience global instance for easy access to definitions and licensed material.
SEMANTICS = Semantics(language="en")
