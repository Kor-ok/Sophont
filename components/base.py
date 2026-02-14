from __future__ import annotations

import dataclasses
from functools import lru_cache
from typing import Any, Union

from humaniseT5.definitions.api import (
    get_alias_map_by_signature,
    get_attribute_by_name,
)


@lru_cache(maxsize=200)
def _compute_signature(
    instance: Any,
) -> tuple[int, ...]:
    """Return a flattened tuple of primitive field values for *instance*,
    preserving declaration order.

    First value of the signature is the subclass index for the instance's class.

    Recursively expands nested ``Primitive`` instances to extract their
    primitive values.

    EXAMPLE: for a ``CharacteristicCode(Primitive)`` with
    ``upp_position=1, subtype=0, category=1`` the result is ``(1, 0, 1)``.

    EXAMPLE: for a ``KnowledgeCode(Primitive)`` with
    ``key=41, focus=-99, associated_skill=SkillCode(key=25, set=1, group=-99)``, the
    result is ``(41, -99, 25, 1, -99)``.
    """
    result: list[int] = []

    # First, append the subclass index for the instance's class to the result.
    subclass_index = instance.subclass_dict.get(instance.__class__.__name__)
    if subclass_index is None:
        raise ValueError(f"Class {instance.__class__.__name__} not found in subclass_dict.")
    result.append(subclass_index)

    try:
        instance_fields = dataclasses.fields(instance)
    except TypeError:
        return tuple(result)

    for f in instance_fields:
        value = getattr(instance, f.name)
        if isinstance(value, Primitive):
            result.extend(_compute_signature(value))
        else:
            result.append(value)
    
    return tuple(result)

def generate_member_dict(instance: Any) -> dict[int, Union[str, type]]:
    """Generate a dict mapping field index to field name for a component class."""
    member_dict = {}
    for attr_name in instance.mro()[0].__annotations__.keys():
        # of_type = instance.mro()[0].__annotations__[attr_name]
        # print(f"Processing attribute '{attr_name}' of type '{of_type}' for class '{instance.__name__}'")
        # included_types = (int,)
        # if of_type in included_types:
        member_dict[len(member_dict)] = attr_name
    # print(f"Generated member_dict for {instance.__name__}: {member_dict}")
    return member_dict

class Primitive:
    """Base class where the child class' signature can be used
    to return their defined name from semantic layer utilities.

    i.e. a CharacteristicCode(Primitive) with upp_position 1, subtype 0, and
    category 1 would have a signature that can fetch "strength" as
    mapped by the semantic layer.

    ``signature`` is an attribute computed automatically by the
    ``@component`` decorator for each concrete subclass — a flattened tuple
    of primitive field values preserving declaration order.
    """
    subclass_dict: dict[str, int] = {}

    def __init_subclass__(cls) -> None:
        """Automatically populate the subclass_dict with each new subclass,
        making sure not to duplicate entries.
        
        The subclass_dict maps the name of each direct subclass to a unique integer index,
        which will be used for DOTS signatures and efficient lookups using the semantic layer.
        """
        if cls.__name__ not in cls.subclass_dict:
            cls.subclass_dict[cls.__name__] = len(cls.subclass_dict)

        # add signature type hint to the subclass
        cls.signature: tuple[int, ...]
        
        """Automatically populate the member_dict with each new subclass, mapping field index
          to field name."""
        # Avoid regenerating the member_dict entry if it already exists, since it is the same for all instances of the class. We can check for this by looking for the presence of the member_dict attribute on the class.
        if not hasattr(cls, "member_dict"):
            cls.member_dict = generate_member_dict(cls)

        cls.member_dict: dict[int, Union[str, type]]

    @property
    def semantics(self) -> Any:
        """Fetch the semantics of this component from the semantic layer using
        its signature and field values.
        """
        from components.definitions import SEMANTICS  # lazy to avoid circular import

        return get_alias_map_by_signature(
            self.__class__,
            self.signature,
            search_index=SEMANTICS.canonical_definitions,
        )

    @classmethod
    def by_name(cls, name: str) -> Primitive:
        """Factory method to create an instance of the child class by alias lookup.
        E.g. for a CharacteristicCode with alias "Strength", will return an instance
        with the correct signature values for that alias.
        """
        from components.definitions import SEMANTICS  # lazy to avoid circular import

        component_attribute_info = get_attribute_by_name(
            cls, name, search_index=SEMANTICS.canonical_definitions
        )
        """
        class ComponentAttributeInfo(NamedTuple):
            name: str
            # Name of the attribute domain used elsewhere, e.g. 'subtype' in CharacteristicCode.
            signature: Signature
            # The attribute's signature, i.e. the flattened tuple of primitive types
        
        To create the new object, we apply the sequence of signature values to each 
        field in the class, in declaration order. We can get the field names and 
        types from dataclasses.fields(cls).
        """
        # Conditional check that cls is a dataclass and has fields, otherwise we can't proceed with this method.
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"Class {cls.__name__} must be a dataclass to use by_name factory method.")
        field_names = [f.name for f in dataclasses.fields(cls)] 
        sig = component_attribute_info.signature
        
        return cls(**{
            **{name: value for name, value in zip(field_names[:-1], sig)},
            field_names[-1]: tuple(sig[len(field_names) - 1 :]),
        })


class Applied:
    """Base class for all components of a more complex signature
    that can hold references to Primitive components or other
    Applied components.
    """

    pass
