from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


class SomeBaseClass:
    
    # Force the child to have a new attribute that is not defined in the dataclass fields, to test that it is preserved and accessible.
    def __post_init__(self):
        self.new_attribute = "This is a new attribute added in the child class."
             

@dataclass
class SomeDataClass(SomeBaseClass):
    field1: int
    field2: float
    field3: str

instance = SomeDataClass(field1=42, field2=3.14, field3="hello")

# access the fields in a more generic way
inspect_attributes = instance.__dict__.items()
print("Inspecting dataclass fields:")
for attr, value in inspect_attributes:
    print(f"{attr}: {value}")


inspect_new_attribute = instance.new_attribute
print(f"Accessing new attribute from base class: {inspect_new_attribute}")