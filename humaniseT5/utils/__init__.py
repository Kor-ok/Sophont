from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from typing import Any, Generic, TypeVar, Union

import pandas as pd
from typing_extensions import Self, TypeAlias


def _iterable_type_checker(input_value: Any) -> Any:
    """Helper function to check if the input value is an iterable of a specific shape of types."""
    if isinstance(input_value, list):
        if all(isinstance(item, int) for item in input_value):
            return list[int]
        elif all(isinstance(item, str) for item in input_value):
            return list[str]
    elif isinstance(input_value, tuple):
        if all(isinstance(item, int) for item in input_value):
            return tuple[int, ...] # Flat tuple of ints
        elif all(isinstance(item, (int, tuple)) for item in input_value):
            return NestedIntTuple # Nested tuple of ints
    return type(input_value)

def _sanitise_input_for_ast_literal_eval(x: Any, type: type) -> Any:
    """Helper function to sanitise input for ast.literal_eval, which can be strict about certain formats."""
    if isinstance(x, str):
        x = x.strip()
        # If the string looks like a list or tuple but isn't properly formatted, try to fix it.
        if (x.startswith("[") and x.endswith("]")) or (x.startswith("(") and x.endswith(")")):
            try:
                return ast.literal_eval(x)
            except Exception:
                pass
        else:
            # print(f"Input '{x}' is not in a list or tuple format. Attempting to sanitise based on expected type {type}.")
            if type == list[str]:
                # This means the input doesn't have "" around the strings between commas, so 
                # we can try to add them and evaluate again.
                regex = r'(?<!")\b(\w+)\b(?!")' # Matches unquoted words
                # Check if there are any unquoted words in the string list input
                if re.search(regex, x):
                    corrected_list_str = re.sub(regex, r'"\1"', x) # Add quotes around unquoted words
                try:
                    return ast.literal_eval(f"[{corrected_list_str}]")
                except Exception:
                    pass
            elif type == list[int]:
                # We need to ensure that the input is in the format of a list of integers, e.g. "1, 2, 3" should become "[1, 2, 3]".
                if not x.startswith("[") and not x.endswith("]"):
                    corrected_list_str = f"[{x}]"
                    try:
                        return ast.literal_eval(corrected_list_str)
                    except Exception:
                        pass
            # if type is list then add the square brackets and if type is tuple then add the parentheses
            elif type is list:
                try:
                    return ast.literal_eval(f"[{x}]")
                except Exception:
                    pass
            elif type is tuple:
                try:             
                    return ast.literal_eval(f"({x})")
                except Exception:
                    pass
    return x

T = TypeVar("T", covariant=True)

NestedIntTuple: TypeAlias = tuple[Union[int, "NestedIntTuple"], ...]
ConvertersType: TypeAlias = Union[Mapping[Union[int, str], Any], None]

class AuthoredValue(Generic[T]):
    """Holds a runtime value while preserving a typing hint so typing.get_args(...)
    can retrieve the carried type via instance.__orig_class__.
    """
    def __init__(self, type_arg: Any, value: Any) -> None:
        # Prefer creating a parameterised Generic so typing.get_args(instance.__orig_class__)
        # returns the supplied type_arg. If that fails, expose a lightweight proxy with __args__.
        try:
            # e.g. AuthoredValue[list[int]] or AuthoredValue[tuple[int, ...]]
            self.__orig_class__ = AuthoredValue[type_arg]  # type: ignore[index]
        except Exception:
            proxy = type("_AuthoredValueProxy", (), {})()
            setattr(proxy, "__args__", (type_arg,))
            self.__orig_class__ = proxy
        self.value = value

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._value = value

    # When a caller references the instance without further arguments, 
    # return the actual carried value NOT the AuthoredValue instance itself.
    def __getattribute__(self, name: str) -> Any:
        if name == "__value__":
            return super().__getattribute__("value")
        return super().__getattribute__(name)
    
    def __repr__(self) -> str:
        return repr(self.value)

class Converters:

    @staticmethod
    def to_python_int(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        return AuthoredValue(int, x)

    @staticmethod
    def list_int(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        val = _sanitise_input_for_ast_literal_eval(x, list[int])
        this_type = list[int]
        value = AuthoredValue(this_type, val)
        return value

    @staticmethod
    def to_str(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        this_type = str
        value = AuthoredValue(this_type, x)
        return value

    @staticmethod
    def list_str(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        val = _sanitise_input_for_ast_literal_eval(x, list[str])
        this_type = list[str]
        value = AuthoredValue(this_type, val)
        return value

    @staticmethod
    def tuple_ints(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        val = _sanitise_input_for_ast_literal_eval(x, tuple)
        this_type = _iterable_type_checker(val)
        value = AuthoredValue(this_type, val)
        return value
    
    @staticmethod
    def to_python_bool(x) -> None | AuthoredValue:
        if pd.isna(x):
            return None
        val = x
        this_type = bool
        value = AuthoredValue(this_type, val)
        return value
    
