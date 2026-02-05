from __future__ import annotations

import inspect
import sys
import threading
from dataclasses import Field, dataclass, field, fields
from typing import (
    Any,
    Callable,
    Protocol,
    TypeVar,
    overload,
    runtime_checkable,
)

# dataclass_transform tells static type checkers that @component behaves like @dataclass
if sys.version_info >= (3, 11):
    from typing import dataclass_transform
else:
    from typing_extensions import dataclass_transform

"""
@component(
    flyweight=True,              # Enable/disable instance caching (default: True)
    validate=True,               # Enable/disable validation (default: True)
    apply_undefined_defaults=True,  # Auto-fill missing int fields with -99
    **dataclass_kwargs           # Pass-through to @dataclass
)
"""
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_UNDEFINED_CODE: int = -99
"""Sentinel value used when a coded field has no meaningful value yet."""

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Thread-safe Component Type Registry (Flyweight Support)
# ---------------------------------------------------------------------------

_component_registry_lock = threading.Lock()
_component_registry: dict[type[Any], dict[tuple[Any, ...], Any]] = {}
"""Maps each component type to its flyweight cache (field values tuple -> instance)."""

_component_types: set[type[Any]] = set()
"""Set of all registered component types for introspection."""


def get_registered_component_types() -> frozenset[type[Any]]:
    """Return an immutable view of all registered component types."""
    with _component_registry_lock:
        return frozenset(_component_types)


def get_flyweight_cache(component_type: type[_T]) -> dict[tuple[Any, ...], _T]:
    """Return the flyweight cache for a given component type (for debugging/introspection)."""
    with _component_registry_lock:
        return dict(_component_registry.get(component_type, {}))


def clear_flyweight_cache(component_type: type[Any] | None = None) -> None:
    """Clear the flyweight cache for a component type, or all if None."""
    with _component_registry_lock:
        if component_type is None:
            for cache in _component_registry.values():
                cache.clear()
        elif component_type in _component_registry:
            _component_registry[component_type].clear()


# ---------------------------------------------------------------------------
# Validation Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Validatable(Protocol):
    """Protocol for components that define custom validation logic."""

    def __validate__(self) -> None:
        """Raise ValueError or TypeError if the instance state is invalid."""
        ...


# ---------------------------------------------------------------------------
# Field-level Validator Support
# ---------------------------------------------------------------------------


def validated_field(
    *,
    default: Any = ...,
    default_factory: Callable[[], Any] | None = None,
    validator: Callable[[Any], None] | None = None,
    **field_kwargs: Any,
) -> Any:
    """Create a dataclass field with an attached validator.

    The validator callable is stored in field.metadata under 'validator'.
    It should raise ValueError or TypeError on invalid input.

    Args:
        default: Default value for the field (mutually exclusive with default_factory).
        default_factory: Factory for mutable defaults (mutually exclusive with default).
        validator: Optional callable(value) -> None that raises on invalid value.
        **field_kwargs: Additional keyword arguments passed to dataclasses.field().

    Returns:
        A dataclass field descriptor with validator metadata attached.
    """
    metadata = dict(field_kwargs.pop("metadata", {}) or {})
    if validator is not None:
        metadata["validator"] = validator

    if default_factory is not None:
        return field(default_factory=default_factory, metadata=metadata, **field_kwargs)
    elif default is not ...:
        return field(default=default, metadata=metadata, **field_kwargs)
    else:
        return field(metadata=metadata, **field_kwargs)


def _run_field_validators(instance: Any, cls_fields: tuple[Field[Any], ...]) -> None:
    """Execute all field-level validators defined in metadata."""
    for f in cls_fields:
        validator = f.metadata.get("validator") if f.metadata else None
        if validator is not None:
            value = getattr(instance, f.name)
            try:
                validator(value)
            except (ValueError, TypeError) as e:
                raise type(e)(f"Field '{f.name}': {e}") from e


# ---------------------------------------------------------------------------
# Utility: Apply undefined defaults
# ---------------------------------------------------------------------------


def _apply_undefined_defaults(
    cls_fields: tuple[Field[Any], ...],
    init_kwargs: dict[str, Any],
) -> dict[str, Any]:
    """For int fields without a default that are missing from kwargs, inject DEFAULT_UNDEFINED_CODE."""
    result = dict(init_kwargs)
    for f in cls_fields:
        if f.name in result:
            continue
        # Only fill in for fields that have no default and are typed as int
        if f.default is not ... or f.default_factory is not None:  # type: ignore[misc]
            continue
        # Check type annotation for int
        if f.type in (int, "int"):
            result[f.name] = DEFAULT_UNDEFINED_CODE
    return result


# ---------------------------------------------------------------------------
# Slots Emulation for Python 3.9
# ---------------------------------------------------------------------------


def _make_slotted_class(
    cls: type[_T],
    slot_names: tuple[str, ...],
    class_vars: dict[str, Any],
) -> type[_T]:
    """Create a new class with __slots__ defined, inheriting from the original.

    This is necessary because __slots__ must be defined at class creation time.
    For Python 3.10+ with dataclass(slots=True), this is handled natively.
    """
    # Build new namespace with __slots__
    namespace: dict[str, Any] = {"__slots__": slot_names, "__module__": cls.__module__}

    # Preserve class-level attributes that should carry over
    for key in ("__doc__", "__validate__"):
        if key in cls.__dict__:
            namespace[key] = cls.__dict__[key]

    # Preserve ClassVar annotations and values
    for name, value in class_vars.items():
        namespace[name] = value

    # Create the new slotted class
    slotted_cls: type[_T] = type(cls.__name__, (cls,), namespace)  # type: ignore[assignment]

    # Copy over qualname for better repr
    slotted_cls.__qualname__ = cls.__qualname__

    return slotted_cls


# ---------------------------------------------------------------------------
# The @component Decorator
# ---------------------------------------------------------------------------


# Overload for @component (no parentheses)
@overload
def component(_cls: type[_T]) -> type[_T]: ...


# Overload for @component(...) (with parentheses)
@overload
def component(
    _cls: None = None,
    *,
    flyweight: bool = ...,
    validate: bool = ...,
    apply_undefined_defaults: bool = ...,
    **dataclass_kwargs: Any,
) -> Callable[[type[_T]], type[_T]]: ...


@dataclass_transform(frozen_default=True)
def component(
    _cls: type[Any] | None = None,
    *,
    flyweight: bool = True,
    validate: bool = True,
    apply_undefined_defaults: bool = True,
    **dataclass_kwargs: Any,
) -> type[Any] | Callable[[type[Any]], type[Any]]:
    """Decorator for ECS-style immutable, slotted, flyweight components.

    Wraps a class with @dataclass(frozen=True, ...) and provides:
      - **Slots emulation** for Python 3.9 (native slots in 3.10+).
      - **Thread-safe flyweight interning**: repeated instantiation with the
        same field values returns the cached instance.
      - **Validation hooks**: if the class defines `__validate__(self) -> None`,
        it is called after construction. Field-level validators in metadata are
        also executed.
      - **Undefined-code defaults**: if `apply_undefined_defaults=True`, missing
        int-typed fields receive `DEFAULT_UNDEFINED_CODE` (-99).
      - **Automatic registration** in a global component type registry.

    Args:
        _cls: The class being decorated (when used without parentheses).
        flyweight: If True (default), cache and reuse instances by field values.
        validate: If True (default), run __validate__ and field validators.
        apply_undefined_defaults: If True, fill missing int fields with -99.
        **dataclass_kwargs: Additional kwargs forwarded to @dataclass (except
            frozen, which is always True).

    Returns:
        The decorated component class.

    Example:
        @component
        class CharacteristicCode:
            upp_position: int
            subtype: int
            category: int

        # Flyweight behavior:
        a = CharacteristicCode(1, 2, 3)
        b = CharacteristicCode(1, 2, 3)
        assert a is b  # Same instance
    """

    def wrap(cls: type[Any]) -> type[Any]:
        # -----------------------------------------------------------------
        # 1. Force frozen=True, handle slots for Python version
        # -----------------------------------------------------------------
        dataclass_kwargs["frozen"] = True

        # Python 3.10+ supports slots=True natively
        use_native_slots = sys.version_info >= (3, 10)
        if use_native_slots:
            dataclass_kwargs.setdefault("slots", True)

        # Apply @dataclass
        dc_cls: type[Any] = dataclass(**dataclass_kwargs)(cls)
        cls_fields: tuple[Field[Any], ...] = fields(dc_cls)
        field_names = tuple(f.name for f in cls_fields)

        # -----------------------------------------------------------------
        # 2. Emulate slots for Python 3.9
        # -----------------------------------------------------------------
        if not use_native_slots:
            # Identify ClassVar items to preserve
            annotations = getattr(dc_cls, "__annotations__", {})
            class_vars: dict[str, Any] = {}
            for name, annotation in annotations.items():
                annotation_str = str(annotation)
                if "ClassVar" in annotation_str:
                    if hasattr(dc_cls, name):
                        class_vars[name] = getattr(dc_cls, name)

            dc_cls = _make_slotted_class(dc_cls, field_names, class_vars)
            # Re-apply dataclass to the slotted subclass for proper init/repr
            dc_cls = dataclass(frozen=True)(dc_cls)
            cls_fields = fields(dc_cls)

        # -----------------------------------------------------------------
        # 3. Thread-safe flyweight registration
        # -----------------------------------------------------------------
        with _component_registry_lock:
            _component_types.add(dc_cls)
            if flyweight:
                _component_registry[dc_cls] = {}

        # -----------------------------------------------------------------
        # 4. Override __new__ for flyweight caching + validation
        # -----------------------------------------------------------------
        original_init = dc_cls.__init__

        if flyweight:

            def __new__(cls_inner: type[Any], *args: Any, **kwargs: Any) -> Any:
                # Handle positional args -> kwargs mapping
                bound_kwargs = dict(kwargs)
                for i, arg in enumerate(args):
                    if i < len(field_names):
                        bound_kwargs[field_names[i]] = arg

                # Optionally apply undefined defaults
                if apply_undefined_defaults:
                    bound_kwargs = _apply_undefined_defaults(cls_fields, bound_kwargs)

                # Build cache key from field values (use defaults for missing)
                cache_key_parts: list[Any] = []
                for f in cls_fields:
                    if f.name in bound_kwargs:
                        cache_key_parts.append(bound_kwargs[f.name])
                    elif f.default is not ...:  # type: ignore[comparison-overlap]
                        cache_key_parts.append(f.default)
                    elif f.default_factory is not None:  # type: ignore[misc]
                        cache_key_parts.append(f.default_factory())  # type: ignore[misc]
                    else:
                        # Missing required field - let dataclass raise
                        cache_key_parts.append(None)

                # Convert mutable items in cache key to hashable form
                cache_key = tuple(
                    tuple(v) if isinstance(v, (list, set)) else v for v in cache_key_parts
                )

                with _component_registry_lock:
                    cache = _component_registry[cls_inner]
                    if cache_key in cache:
                        return cache[cache_key]

                    # Create new instance
                    instance = object.__new__(cls_inner)
                    # Store in cache before init (to handle recursive refs)
                    cache[cache_key] = instance

                return instance

            # Preserve the signature on __new__ so inspect.signature(ClassName) works
            try:
                # Build signature for __new__: (cls, field1, field2, ...) -> ClassName
                init_sig = inspect.signature(original_init)
                # Replace 'self' with 'cls' for __new__
                new_params = [inspect.Parameter("cls", inspect.Parameter.POSITIONAL_OR_KEYWORD)] + [
                    p for name, p in init_sig.parameters.items() if name != "self"
                ]
                __new__.__signature__ = init_sig.replace(parameters=new_params)  # type: ignore[attr-defined]
            except (ValueError, TypeError):
                pass

            dc_cls.__new__ = __new__  # type: ignore[assignment]

        # -----------------------------------------------------------------
        # 5. Wrap __init__ to run validation after field assignment
        # -----------------------------------------------------------------
        if validate:

            def validated_init(self: Any, *args: Any, **kwargs: Any) -> None:
                # Check if already initialized (flyweight cache hit)
                if flyweight:
                    try:
                        # If any field is already set, this is a cache hit
                        if cls_fields and hasattr(self, field_names[0]):
                            getattr(self, field_names[0])
                            return  # Already initialized
                    except AttributeError:
                        pass  # Not yet initialized

                # Apply undefined defaults if needed
                if apply_undefined_defaults:
                    kwargs = _apply_undefined_defaults(cls_fields, kwargs)

                original_init(self, *args, **kwargs)

                # Run field-level validators
                _run_field_validators(self, cls_fields)

                # Run class-level __validate__ if defined
                if hasattr(self, "__validate__") and callable(self.__validate__):
                    self.__validate__()

            # Preserve the original __init__ signature so IDEs/type-checkers see constructor params
            try:
                validated_init.__signature__ = inspect.signature(original_init)  # type: ignore[attr-defined]
                validated_init.__doc__ = original_init.__doc__
                validated_init.__name__ = original_init.__name__
                validated_init.__qualname__ = original_init.__qualname__
            except (ValueError, TypeError):
                pass  # Best effort - some built-in inits don't have inspectable signatures

            dc_cls.__init__ = validated_init  # type: ignore[method-assign]

        # -----------------------------------------------------------------
        # 6. Add immutability enforcement
        # -----------------------------------------------------------------
        def __setattr_frozen__(self: Any, name: str, value: Any) -> None:
            # Allow setting during __init__ (frozen dataclass handles this)
            raise AttributeError(f"Cannot modify immutable component '{dc_cls.__name__}'")

        # The frozen dataclass already handles this, but we ensure it's set
        if not hasattr(dc_cls, "__delattr__") or dc_cls.__delattr__ is object.__delattr__:

            def __delattr_frozen__(self: Any, name: str) -> None:
                raise AttributeError(
                    f"Cannot delete attribute from immutable component '{dc_cls.__name__}'"
                )

            dc_cls.__delattr__ = __delattr_frozen__  # type: ignore[method-assign]

        # -----------------------------------------------------------------
        # 7. Add utility methods
        # -----------------------------------------------------------------
        def _as_tuple(self: Any) -> tuple[Any, ...]:
            """Return field values as a tuple (useful for hashing/comparison)."""
            return tuple(getattr(self, f.name) for f in cls_fields)

        def _cache_key(self: Any) -> tuple[Any, ...]:
            """Return the cache key used for flyweight lookup."""
            return tuple(
                tuple(v) if isinstance(v, (list, set)) else v
                for v in (getattr(self, f.name) for f in cls_fields)
            )

        dc_cls._as_tuple = _as_tuple  # type: ignore[attr-defined]
        dc_cls._cache_key = _cache_key  # type: ignore[attr-defined]

        return dc_cls

    # Support both @component and @component(...)
    return wrap if _cls is None else wrap(_cls)
