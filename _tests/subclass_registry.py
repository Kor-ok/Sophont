from __future__ import annotations

import sys
from pathlib import Path
from pprint import pprint

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from semantics.definitions import SEMANTICS


def test_base_class_subclass_dict():
    from semantics.base import Primitive
    # Get a list of all subclasses of Primitive
    subclasses = Primitive.__subclasses__()
    subclass_dict: dict[str, int] = {subclass.__name__: index for index, subclass in enumerate(subclasses)}
    print("Externally computed subclass_dict:")
    pprint(subclass_dict, indent=2)
    print("\nSubclass dict from the base class itself:")
    pprint(Primitive.subclass_dict, indent=2)
    print("\nEquality Test:")
    print(subclass_dict == Primitive.subclass_dict)

def test_get_base_class_subclass_dict_from_child_instances():
    from semantics.base import Primitive
    from semantics.data import (
        CharacteristicCode,
        GenderCode,
        KnowledgeCode,
        SkillCode,
    )
    example_subclasses = [
        CharacteristicCode(upp_position=1, subtype=0, category=1),
        GenderCode(key=1),
        SkillCode(key=21, set=1, group=1),
        KnowledgeCode(key=41, focus=-99, associated_skill=SkillCode(key=25, set=1, group=-99)),
    ]
    # Get the base class subclass_dict from the instances
    for example in example_subclasses:
        base_subclass_dict = example.__class__.subclass_dict
        print(f"\nSubclass dict from the instance of {example.__class__.__name__}:")
        pprint(base_subclass_dict, indent=2)
        # Check if the base class subclass_dict is the same as the one from the instance
        print(f"Is the base class subclass_dict the same as the instance's subclass_dict?")
        print(base_subclass_dict == Primitive.subclass_dict)

    # Get the subclass_dict value from the child instance by using the child instance
    for example in example_subclasses:
        subclass_dict_value = example.__class__.subclass_dict.get(example.__class__.__name__)
        print(f"\nSubclass dict value for {example.__class__.__name__}: {subclass_dict_value}")

    print("\n")
    constructed_name = CharacteristicCode.__module__ + "." + CharacteristicCode.__name__
    print(f"\nConstructed Name: {constructed_name}")
    direct_name = CharacteristicCode.__annotations__
    print(f"\nDirect name: {direct_name}")

if __name__ == "__main__":
    # test_base_class_subclass_dict()
    test_get_base_class_subclass_dict_from_child_instances()

