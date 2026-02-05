"""
                    ┌─────────────────────────────────────┐
                    │         AppliedAttributeBase        │
                    │  (thread-safe cache, immutability)  │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌────────────────────────┐
│  FullCodeAttribute  │   │  CompositeAttribute │   │ CollectionComposite    │
│  (leaf flyweights)  │   │  (wrap 1 attribute) │   │ (aggregate flyweights) │
├─────────────────────┤   ├─────────────────────┤   ├────────────────────────┤
│ • Characteristic    │   │ • Gene              │   │ • Genotype             │
│ • Skill             │   │ • Phene             │   │ • AttributePackage     │
│ • Knowledge         │   │                     │   │                        │
└─────────────────────┘   └─────────────────────┘   └────────────────────────┘
"""

from __future__ import annotations

import threading
from typing import (
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from components.primitives.data import CanonicalStrKey, FullCode, StringAliases

# -----------------------------------------------------------------------------
# Type Variables
# -----------------------------------------------------------------------------

K = TypeVar("K")  # Cache key type
T = TypeVar("T", bound="AppliedAttributeBase[Any]")  # Self-referential for returns


# -----------------------------------------------------------------------------
# Protocols for Composite Pattern
# -----------------------------------------------------------------------------


@runtime_checkable
class FullCodeAttribute(Protocol):
    """
    Protocol for attributes keyed by a FullCode tuple (3 ints).

    Implemented by: Characteristic, Skill, Knowledge
    """

    def get_code(self) -> FullCode:
        """Return the (primary, secondary, tertiary) code tuple."""
        ...

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Return (canonical_name, aliases) for this attribute."""
        ...

    @classmethod
    def by_name(cls, name: str) -> FullCodeAttribute:
        """Factory: construct flyweight by canonical name or alias lookup."""
        ...

    @classmethod
    def by_code(cls, code: FullCode) -> FullCodeAttribute:
        """Factory: construct flyweight by FullCode tuple."""
        ...


@runtime_checkable
class CompositeAttribute(Protocol):
    """
    Protocol for attributes that wrap/compose another attribute.

    Implemented by: Gene, Phene (which wrap a Characteristic)
    """

    @property
    def characteristic(self) -> FullCodeAttribute:
        """The wrapped characteristic this composite is based on."""
        ...

    def get_code(self) -> FullCode:
        """Delegate to the wrapped characteristic's code."""
        ...

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Delegate to the wrapped characteristic's name."""
        ...


# -----------------------------------------------------------------------------
# Thread-Safe Flyweight Base Class
# -----------------------------------------------------------------------------


class AppliedAttributeBase(Generic[K]):
    """
    Base class for applied attributes like Characteristic/Gene/Phene/Skill/Knowledge.

    Provides:
        1) Thread-safe flyweight caching logic with per-class RLock.
        2) Immutability guard via __setattr__ override.
        3) Protected attribute setting via _set_attr helper.
        4) Cache management helpers: _cache_get, _cache_set, _cache_get_or_create.

    Subclasses must define:
        - __slots__ for their specific fields
        - Key: TypeAlias for their cache key type
        - _make_key(...) -> K classmethod to normalise constructor args to cache key
        - _init_from_key(key: K) to set attributes from the cache key

    Composite Pattern roles:
        - Characteristic, Skill, Knowledge → implement FullCodeAttribute protocol
        - Gene, Phene → implement CompositeAttribute protocol
        - Package, Genotype → use AppliedAttributeBase only
    """

    __slots__ = ()

    # Subclasses override these; declared here for type-checking visibility.
    Key: ClassVar[type] = tuple  # Override with actual key TypeAlias
    _cache: ClassVar[dict[Any, Any]]  # dict[K, Self] - subclass defines
    _cache_lock: ClassVar[threading.RLock]  # Per-class lock for thread safety

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Automatically provision per-class cache and lock when subclassing.

        This ensures each concrete subclass gets its own isolated cache dict
        and RLock, avoiding shared state between different attribute types.
        """
        super().__init_subclass__(**kwargs)

        # Only provision if the subclass doesn't already define its own
        if "_cache" not in cls.__dict__:
            cls._cache = {}
        if "_cache_lock" not in cls.__dict__:
            cls._cache_lock = threading.RLock()

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent mutation of flyweight instances after creation."""
        raise AttributeError(
            f"{self.__class__.__name__} instances are immutable; " f"cannot set attribute '{name}'"
        )

    def __delattr__(self, name: str) -> None:
        """Prevent deletion of attributes on flyweight instances."""
        raise AttributeError(
            f"{self.__class__.__name__} instances are immutable; "
            f"cannot delete attribute '{name}'"
        )

    # -------------------------------------------------------------------------
    # Protected helpers for subclass use
    # -------------------------------------------------------------------------

    def _set_attr(self, name: str, value: object) -> None:
        """
        Bypass __setattr__ guard to set an attribute during __new__.

        Subclasses call this in __new__ to initialise immutable fields:
            self._set_attr("field_name", value)
        """
        object.__setattr__(self, name, value)

    @classmethod
    def _cache_get(cls: type[T], key: K) -> T | None:
        """
        Thread-safe lookup in the flyweight cache.

        Returns the cached instance if present, else None.
        """
        with cls._cache_lock:
            return cls._cache.get(key)  # type: ignore[return-value]

    @classmethod
    def _cache_set(cls: type[T], key: K, instance: T) -> None:
        """
        Thread-safe insertion into the flyweight cache.

        Should only be called once per unique key, after instance creation.
        """
        with cls._cache_lock:
            cls._cache[key] = instance  # type: ignore[index]

    @classmethod
    def _cache_get_or_create(
        cls: type[T],
        key: K,
        factory: Any = None,
    ) -> tuple[T | None, bool]:
        """
        Thread-safe cache lookup with optional creation placeholder.

        Returns:
            (cached_instance, True) if key was already in cache.
            (None, False) if key is new and caller should create instance.

        Usage pattern in subclass __new__:
            key = cls._make_key(args...)
            cached, found = cls._cache_get_or_create(key)
            if found:
                return cached
            # Create new instance, then call cls._cache_set(key, self)
        """
        with cls._cache_lock:
            cached = cls._cache.get(key)
            if cached is not None:
                return cached, True  # type: ignore[return-value]
            return None, False

    # -------------------------------------------------------------------------
    # Abstract/template methods for subclasses to implement
    # -------------------------------------------------------------------------

    @classmethod
    def _make_key(cls, *args: Any, **kwargs: Any) -> K:
        """
        Normalise constructor arguments into a hashable cache key.

        Subclasses MUST override this to define their key structure.
        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(f"{cls.__name__} must implement _make_key classmethod")

    def _init_from_key(self, key: K) -> None:
        """
        Initialise instance attributes from the cache key.

        Subclasses MAY override if key contains all needed data.
        Called after instance creation in __new__ pattern.
        """
        pass  # Default: no-op; subclass can override

    # -------------------------------------------------------------------------
    # Introspection helpers
    # -------------------------------------------------------------------------

    @classmethod
    def cache_size(cls) -> int:
        """Return the number of cached instances for this attribute type."""
        with cls._cache_lock:
            return len(cls._cache)

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached instances for this attribute type.

        WARNING: This breaks flyweight identity guarantees. Use only for
        testing or when deliberately resetting application state.
        """
        with cls._cache_lock:
            cls._cache.clear()

class AttributeSpecMixin:
    """
    Mixin that:
      - defines ATTRS = {name: default}
      - auto-generates __slots__
      - auto-handles __new__
      - auto-builds flyweight keys
      - auto-calls _set_attr
    """

    ATTRS: dict[str, object] = {}
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        # Resolve args + defaults
        values = cls._resolve_args(args, kwargs)

        # Build key in a consistent order
        key = tuple(values[name] for name in cls.ATTRS)

        # Use the base class cache
        cached, found = cls._cache_get_or_create(key) # type: ignore
        if found:
            return cached

        # Create instance
        self = super().__new__(cls)

        # Set attributes immutably
        for name, value in values.items():
            self._set_attr(name, value) # type: ignore

        cls._cache_set(key, self) # type: ignore
        return self

    @classmethod
    def _resolve_args(cls, args, kwargs):
        names = list(cls.ATTRS.keys())
        defaults = cls.ATTRS

        values = defaults.copy()

        # Positional args
        for name, value in zip(names, args):
            values[name] = value

        # Keyword args
        for name, value in kwargs.items():
            if name not in defaults:
                raise TypeError(f"Unexpected argument {name}")
            values[name] = value

        return values