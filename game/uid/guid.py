from __future__ import annotations

import threading
from collections import OrderedDict
from enum import Enum
from random import randint

"""Utility functions for generating and handling 32-bit Unique Identifiers (GUID) in the game.
"""

# Thread-safe bounded cache for UID-to-string mappings with O(1) lookup
_UID_STRING_CACHE_MAXLEN = 1000
_lock = threading.Lock()
_uid_store: set[int] = set()
_uid_to_string_store: OrderedDict[int, str] = OrderedDict()


class NameSpaces:
    """Totalling 16 bits, defines the branching namespaces for GUID generation and lookup."""

    class Entity(Enum):
        """Of 8 bits, defines the first namespace for the GUID."""

        CHARACTERS = 0o0
        SPECIES = 0o1
        PACKAGES = 0o2
        EVENTS = 0o3

    class Owner(Enum):
        """Of 8 bits, defines the second namespace branching from the first for the GUID."""

        PLAYER = 0o0
        NPC = 0o1
        ENV = 0o2


class GUID:
    """Stateless utility class managing the creation of non-clashing Global Unique Identifiers (GUID) for game entities.

    Namespaces are 8-bits each. The last 16-bits are randomly generated.

    Thread-safe: All operations on the global UID store are protected by a lock.
    """

    @staticmethod
    def _register_string(uid: int, name: str) -> None:
        """Register a UID-to-string mapping, evicting oldest if at capacity.

        Must be called while holding _lock.
        """
        # If already present, move to end (most recently used)
        if uid in _uid_to_string_store:
            _uid_to_string_store.move_to_end(uid)
            _uid_to_string_store[uid] = name
        else:
            # Evict oldest if at capacity
            if len(_uid_to_string_store) >= _UID_STRING_CACHE_MAXLEN:
                _uid_to_string_store.popitem(last=False)
            _uid_to_string_store[uid] = name

    @staticmethod
    def _build_uid(
        ns1: NameSpaces.Entity,
        ns2: NameSpaces.Owner,
        unique_id: int | None = None,
    ) -> int:
        """Construct the raw UID value without side effects."""
        if unique_id is None:
            unique_id = randint(0, 0xFFFF)
        return (ns1.value << 24) | (ns2.value << 16) | unique_id

    @staticmethod
    def _build_name(
        ns1: NameSpaces.Entity,
        ns2: NameSpaces.Owner,
        uid: int,
        name: str | None = None,
    ) -> str:
        """Build the string representation for a UID."""
        if name is not None:
            return f"{ns1.name}.{ns2.name}.{name}"
        return f"{ns1.name}.{ns2.name}.{uid:08X}"

    @staticmethod
    def generate(
        ns1: NameSpaces.Entity,
        ns2: NameSpaces.Owner,
        unique_id: int | None = None,
        name: str | None = None,
    ) -> int:
        """Generate a unique identifier, retrying on collision.

        Thread-safe: uses lock to ensure atomic check-and-add.
        """
        with _lock:
            uid = GUID._build_uid(ns1, ns2, unique_id)

            # Retry with new random suffix on collision (only if unique_id was None)
            attempts = 0
            max_attempts = 0xFFFF  # Prevent infinite loop in pathological cases
            while uid in _uid_store:
                if unique_id is not None:
                    # Caller specified a fixed ID that already exists
                    raise ValueError(
                        f"UID collision: {uid:08X} already exists and unique_id was fixed"
                    )
                attempts += 1
                if attempts > max_attempts:
                    raise RuntimeError("Failed to generate unique ID after max attempts")
                uid = GUID._build_uid(ns1, ns2, None)

            _uid_store.add(uid)
            GUID._register_string(uid, GUID._build_name(ns1, ns2, uid, name))

        return uid

    @staticmethod
    def remove(uid: int) -> bool:
        """Remove a UID from the store. Returns True if it existed, False otherwise.

        Thread-safe.
        """
        with _lock:
            if uid in _uid_store:
                _uid_store.discard(uid)
                _uid_to_string_store.pop(uid, None)
                return True
            return False

    @staticmethod
    def exists(uid: int) -> bool:
        """Check if a UID exists in the store. Thread-safe."""
        with _lock:
            return uid in _uid_store

    @staticmethod
    def parse(uid: int) -> tuple[NameSpaces.Entity, NameSpaces.Owner, int]:
        """Parse a UID into its namespace components. Pure function, no lock needed."""
        ns1 = NameSpaces.Entity((uid >> 24) & 0xFF)
        ns2 = NameSpaces.Owner((uid >> 16) & 0xFF)
        unique_id = uid & 0xFFFF
        return ns1, ns2, unique_id

    @staticmethod
    def uid_to_string(uid: int, full: bool = False) -> str:
        """Look up the string representation of a UID. Thread-safe, O(1) lookup."""
        with _lock:
            name = _uid_to_string_store.get(uid)
        if name is not None:
            return name if full else name.split(".")[-1]
        return f"NotFound_{uid:08X}"

    @staticmethod
    def clear() -> None:
        """Clear all stored UIDs. Useful for testing. Thread-safe."""
        with _lock:
            _uid_store.clear()
            _uid_to_string_store.clear()
