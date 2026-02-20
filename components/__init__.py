from __future__ import annotations

import inspect
import logging
import sys
import threading
from array import array
from dataclasses import Field, dataclass, fields
from typing import (
    Any,
    Callable,
    TypeVar,
    overload,
)

logger = logging.getLogger(__name__)

# dataclass_transform tells static type checkers that @component behaves like @dataclass
if sys.version_info >= (3, 11):
    from typing import dataclass_transform
else:
    from typing_extensions import dataclass_transform

"""
@component(
    flyweight=True,              # Enable/disable instance caching (default: True)
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
    apply_undefined_defaults: bool = ...,
    **dataclass_kwargs: Any,
) -> Callable[[type[_T]], type[_T]]: ...


@dataclass_transform(frozen_default=True)
def component(
    _cls: type[Any] | None = None,
    *,
    flyweight: bool = True,
    apply_undefined_defaults: bool = True,
    **dataclass_kwargs: Any,
) -> type[Any] | Callable[[type[Any]], type[Any]]:
    """Decorator for ECS-style immutable, slotted, flyweight components.

    Wraps a class with @dataclass(frozen=True, ...) and provides:
      - **Slots emulation** for Python 3.9 (native slots in 3.10+).
      - **Thread-safe flyweight interning**: repeated instantiation with the
        same field values returns the cached instance.
      - **Undefined-code defaults**: if `apply_undefined_defaults=True`, missing
        int-typed fields receive `DEFAULT_UNDEFINED_CODE` (-99).
      - **Automatic registration** in a global component type registry.

    Args:
        _cls: The class being decorated (when used without parentheses).
        flyweight: If True (default), cache and reuse instances by field values.
        apply_undefined_defaults: If True, fill missing int fields with -99.
        **dataclass_kwargs: Additional kwargs forwarded to @dataclass (except
            frozen, which is always True).

    Returns:
        The decorated component class.

    Example:
        @component
        class CharacteristicCode(Primitive):
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
        # We are developing for Python 3.9 so handle slots emulation with
        # the following:

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
                        print(f"\033[0;34mCache hit for {cls_inner.__name__} with key {cache_key}\033[0m")
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
        def _semantic_signature(self: Any) -> tuple[int, ...]:
            """Return field values in order as a tuple, expanding nested Primitive/Applied components
            recursively — each recursion returns its values inside its own tuple."""
            
            def expand(value: Any) -> Any:
                base_class = dc_cls.mro()[-2]
                if isinstance(value, base_class):
                    # Prefer calling a bound _semantic_signature if present and callable.
                    if callable(getattr(value, "_semantic_signature", None)):
                        # Access via getattr to satisfy type-checkers that may
                        # not know Primitive/Applied exposes a private attribute.
                        func = getattr(value, "_semantic_signature")
                        return tuple(func())
                    comp = getattr(value, "component_signature", b"")
                    # Semantic signatures do not include the domain identity at the start of the signature,
                    # so we remove it.
                    
                    comp = comp[1:] if isinstance(comp, bytes) and len(comp) > 0 else comp
                    # # Convert bytes to an array of integers for easier handling in the semantic map.
                    # comp = array('b', comp).tolist() if isinstance(comp, bytes) else comp
                    # # Convert the array of integers to a tuple for the semantic signature.
                    # comp = tuple(comp) if isinstance(comp, list) else comp
                    return tuple(expand(v) for v in comp)

                # Preserve and recurse into standard iterables as tuples
                if isinstance(value, (list, set, tuple)):
                    return tuple(expand(v) for v in value)

                return value

            return tuple(expand(getattr(self, f.name)) for f in cls_fields)

        def _cache_key(self: Any) -> tuple[Any, ...]:
            """Return the cache key used for flyweight lookup."""
            return tuple(
                tuple(v) if isinstance(v, (list, set)) else v
                for v in (getattr(self, f.name) for f in cls_fields)
            )
        
        def _component_signature(self: Any) -> array:
            """Return the component signature as an array of bytes."""
            sig = self.component_signature
            # Convert the semantic signature to a flat array of bytes
            if isinstance(sig, bytes):
                return array('b', sig)
            elif isinstance(sig, tuple):
                # Flatten nested tuples and convert to array of bytes
                flat_sig = []
                def flatten(s):
                    for item in s:
                        if isinstance(item, tuple):
                            flatten(item)
                        else:
                            flat_sig.append(item)
                flatten(sig)
                return array('b', flat_sig)
            else:
                raise ValueError(f"Unexpected component signature type: {type(sig)}")

        dc_cls._semantic_signature = _semantic_signature  # type: ignore[attr-defined]
        dc_cls._cache_key = _cache_key  # type: ignore[attr-defined]
        dc_cls._component_signature = _component_signature  # type: ignore[attr-defined]

        # -----------------------------------------------------------------
        # 8. Primitive support — compute signature after init
        # -----------------------------------------------------------------
        # Primitive subclasses gain a ``signature`` attribute: a flattened
        # tuple of primitive field values computed after the frozen dataclass
        # __init__ completes.  The attribute is stored in the instance's
        # __dict__ (inherited from Primitive which has no __slots__) and is
        # deliberately excluded from the dataclass fields, cache key, and
        # slots so it does not affect flyweight identity.
        try:
            from components.base import Primitive, _compute_component_signature

            if issubclass(dc_cls, Primitive):
                _prev_init = dc_cls.__init__

                def _init_with_signature(self: Any, *args: Any, **kwargs: Any) -> None:
                    _prev_init(self, *args, **kwargs)

                    if not hasattr(self, "component_signature"):
                        object.__setattr__(self, "component_signature", _compute_component_signature(self))
                        logger.debug(f"lru_cache info for {dc_cls.__name__}: {_compute_component_signature.cache_info()}")

                    if not hasattr(self, "semantic_signature"):
                        object.__setattr__(self, "semantic_signature", self._semantic_signature())

                # Preserve init signature for IDE / introspection.
                try:
                    _init_with_signature.__signature__ = inspect.signature(  # type: ignore[attr-defined]
                        _prev_init
                    )
                except (ValueError, TypeError):
                    pass

                dc_cls.__init__ = _init_with_signature  # type: ignore[method-assign]

                # Implement type hints for the computed signature attribute
                annotations = dict(getattr(dc_cls, "__annotations__", {}))
                annotations["component_signature"] = "bytes"
                annotations["semantic_signature"] = "tuple[int, ...]"
                dc_cls.__annotations__ = annotations

        except ImportError:
            pass
        
        return dc_cls

    # Support both @component and @component(...)
    return wrap if _cls is None else wrap(_cls)
