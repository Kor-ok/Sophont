from __future__ import annotations

import ast
import re
import types as _types
from collections.abc import Mapping
from typing import Any, Generic, TypeVar, Union

from typing_extensions import TypeAlias

DEFAULT_INT = -99  # Sentinel value for missing/empty int inputs

T = TypeVar("T", covariant=False)

NestedIntTuple: TypeAlias = tuple[Union[int, "NestedIntTuple"], ...]
ConvertersType: TypeAlias = Union[Mapping[Union[int, str], Any], None]


# ---------------------------------------------------------------------------
#  Factory returned by AuthoredValue[T]
# ---------------------------------------------------------------------------


class _AuthoredValueFactory:
    """Callable returned by ``AuthoredValue[T]``.

    Creates :class:`AuthoredValue` instances with the subscripted type
    available during construction for sanitisation and type inference.
    """

    __slots__ = ("_cls", "_type_arg")

    def __init__(self, cls: type, type_arg: Any) -> None:
        self._cls = cls
        self._type_arg = type_arg

    def __call__(self, value: Any) -> AuthoredValue:
        cls = self._cls
        type_arg = self._type_arg

        # --- sanitise string input based on the declared type -------------
        if isinstance(value, str) and type_arg is not str:
            value = cls._sanitise(value, type_arg)

        # --- for bare `tuple`, refine to a concrete parameterised type ----
        effective_type = type_arg
        if effective_type is tuple:
            effective_type = cls._infer_iterable_type(value)

        inst = object.__new__(cls)
        inst._value = value
        inst.__orig_class__ = _types.GenericAlias(cls, (effective_type,))
        return inst

    def __repr__(self) -> str:
        return f"{self._cls.__name__}[{self._type_arg!r}]"


# ---------------------------------------------------------------------------
#  AuthoredValue
# ---------------------------------------------------------------------------


class AuthoredValue(Generic[T]):
    """Holds a runtime value while preserving a typing hint so ``typing.get_args(...)``
    can retrieve the carried type via ``instance.__orig_class__``.

    Instantiate via the subscript syntax to declare the expected type::

        av = AuthoredValue[list[str]]("foo, bar, baz")
        av.value                       # ['foo', 'bar', 'baz']
        get_args(av.__orig_class__)    # (list[str],)

    On construction the raw *value* is automatically sanitised (string inputs
    are coerced to the expected Python literal where possible) and, for
    generic ``tuple`` types, the concrete type annotation is inferred from
    the actual data.
    """

    __slots__ = ("_value", "__orig_class__")

    # Pre-compiled pattern for matching unquoted words (used by list[str] sanitisation).
    _UNQUOTED_WORD_RE: re.Pattern[str] = re.compile(r'(?<!")\b(\w+(?:[- ]\w+)*)\b(?!")')

    @classmethod
    def __class_getitem__(cls, type_arg: Any) -> _AuthoredValueFactory:
        """Return a callable factory that creates instances with *type_arg* baked in."""
        return _AuthoredValueFactory(cls, type_arg)

    def __init__(self, value: Any) -> None:
        """Bare constructor (no subscript type info).

        Prefer ``AuthoredValue[T](value)`` for typed creation.
        """
        self._value = value

    # ------------------------------------------------------------------
    #  Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_iterable_type(input_value: Any) -> Any:
        """Infer the narrowest type annotation for an iterable *input_value*."""
        if isinstance(input_value, list):
            if all(isinstance(item, int) for item in input_value):
                return list[int]
            if all(isinstance(item, str) for item in input_value):
                return list[str]
        elif isinstance(input_value, tuple):
            if all(isinstance(item, int) for item in input_value):
                return tuple[int, ...]
            if all(isinstance(item, (int, tuple)) for item in input_value):
                return NestedIntTuple
        return type(input_value)

    @classmethod
    def _sanitise(cls, x: str, expected_type: Any) -> Any:
        """Coerce a raw string *x* into a Python literal matching *expected_type*.

        Uses ``ast.literal_eval`` where possible; raises ``ValueError`` on
        unparseable input.  Returns *x* unchanged for scalar types (``bool``,
        ``int``) when no conversion applies.
        """
        x = x.strip()

        # --- already looks like a list/tuple literal ----------------------
        if (x.startswith("[") and x.endswith("]")) or (x.startswith("(") and x.endswith(")")):
            try:
                return ast.literal_eval(x)
            except Exception:
                raise ValueError(
                    f"Failed to parse '{x}' as a Python literal "
                    f"for expected type {expected_type}."
                )

        # --- type-specific coercion (bare strings) ------------------------
        if expected_type == list[str]:
            match = cls._UNQUOTED_WORD_RE.search(x)
            corrected = cls._UNQUOTED_WORD_RE.sub(r'"\1"', x) if match else x
            try:
                return ast.literal_eval(f"[{corrected}]")
            except Exception:
                raise ValueError(
                    f"Failed to parse '{x}' as a Python literal "
                    f"for expected type {expected_type}."
                )

        if expected_type in (list[int], list):
            try:
                return ast.literal_eval(f"[{x}]")
            except Exception:
                raise ValueError(
                    f"Failed to parse '{x}' as a Python literal "
                    f"for expected type {expected_type}."
                )

        if expected_type is tuple:
            try:
                return ast.literal_eval(f"({x})")
            except Exception:
                raise ValueError(
                    f"Failed to parse '{x}' as a Python literal "
                    f"for expected type {expected_type}."
                )

        if expected_type is bool and x == "":
            return False

        if expected_type is int and x == "":
            return DEFAULT_INT

        return x

    # ------------------------------------------------------------------
    #  Value access
    # ------------------------------------------------------------------

    @property
    def value(self) -> T:
        """The carried runtime value."""
        return self._value  # type: ignore[return-value]

    def __repr__(self) -> str:
        return repr(self._value)


class Converters:
    """Thin wrappers that declare the expected type; all sanitisation and
    type-inference logic lives inside :class:`AuthoredValue`.
    """

    @staticmethod
    def to_python_int(x) -> AuthoredValue:
        return AuthoredValue[int](x)

    @staticmethod
    def list_int(x) -> AuthoredValue:
        return AuthoredValue[list[int]](x)

    @staticmethod
    def to_str(x) -> AuthoredValue:
        return AuthoredValue[str](x)

    @staticmethod
    def list_str(x) -> AuthoredValue:
        return AuthoredValue[list[str]](x)

    @staticmethod
    def tuple_int(x) -> AuthoredValue:
        return AuthoredValue[tuple](x)

    @staticmethod
    def to_python_bool(x) -> AuthoredValue:
        return AuthoredValue[bool](x)
