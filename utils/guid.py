from __future__ import annotations

import threading
from enum import Enum
from random import getrandbits

"""Utilities for generating and resolving 32-bit GUID values."""

_lock = threading.Lock()
_uid_to_name_store: dict[GUID, str] = {}
_name_to_uid_store: dict[str, GUID] = {}
_uid_to_instance_store: dict[GUID, object] = {}
_instance_id_to_uids: dict[int, list[GUID]] = {}


class GUID(int):
    """Stateless utility class managing the creation of non-clashing Global Unique Identifiers (GUID) for game entities.

    Namespaces are 8-bits each. The last 16-bits are randomly generated.

    Thread-safe: All operations on the global UID store are protected by a lock.
    """

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

    class NameSpaces:
        """Backward-compatible namespace wrapper populated after class definition."""

        Entity: type[GUID.Entity]
        Owner: type[GUID.Owner]

    @staticmethod
    def _register_name(uid: GUID, full_name: str) -> None:
        """Register or update the canonical full name for a UID.

        Must be called while holding _lock.
        """
        previous_name = _uid_to_name_store.get(uid)
        if previous_name is not None and previous_name != full_name:
            _name_to_uid_store.pop(previous_name, None)

        _uid_to_name_store[uid] = full_name
        _name_to_uid_store[full_name] = uid

    @staticmethod
    def _register_instance(uid: GUID, instance: object) -> None:
        """Register or update the instance associated with a UID.

        Must be called while holding _lock.
        """
        previous_instance = _uid_to_instance_store.get(uid)
        if previous_instance is not None:
            previous_instance_id = id(previous_instance)
            previous_uids = _instance_id_to_uids.get(previous_instance_id)
            if previous_uids is not None:
                _instance_id_to_uids[previous_instance_id] = [
                    registered_uid for registered_uid in previous_uids if registered_uid != uid
                ]
                if not _instance_id_to_uids[previous_instance_id]:
                    _instance_id_to_uids.pop(previous_instance_id, None)

        _uid_to_instance_store[uid] = instance

        instance_id = id(instance)
        registered_uids = _instance_id_to_uids.setdefault(instance_id, [])
        if uid not in registered_uids:
            registered_uids.append(uid)

    @staticmethod
    def _build_uid(
        ns1: GUID.Entity,
        ns2: GUID.Owner,
        unique_id: int | None = None,
    ) -> GUID:
        """Construct the raw UID value without side effects."""
        if unique_id is None:
            unique_id = getrandbits(16)
        return GUID((ns1.value << 24) | (ns2.value << 16) | unique_id)

    @staticmethod
    def _build_full_namespace(
        ns1: GUID.Entity,
        ns2: GUID.Owner,
        uid: GUID,
        name: str | None = None,
    ) -> str:
        """Build the full string representation for a UID."""
        if name is not None:
            return f"{ns1.name}.{ns2.name}.{name}"
        return f"{ns1.name}.{ns2.name}.{uid:08X}"

    @staticmethod
    def _parse_uid(uid: GUID) -> tuple[GUID.Entity, GUID.Owner, int]:
        """Parse a raw GUID into namespace components and local id."""
        ns1 = GUID.Entity((uid >> 24) & 0xFF)
        ns2 = GUID.Owner((uid >> 16) & 0xFF)
        unique_id = uid & 0xFFFF
        return ns1, ns2, unique_id

    @staticmethod
    def generate(
        ns1: GUID.Entity,
        ns2: GUID.Owner,
        manual_id: int | None = None,
        name: str | None = None,
        instance: object | None = None,
        *,
        unique_id: int | None = None,
    ) -> GUID:
        """Generate a unique identifier, retrying on collision.

        Thread-safe: uses lock to ensure atomic check-and-add.
        """
        if manual_id is not None and unique_id is not None:
            raise ValueError("Pass either manual_id or unique_id, not both")

        requested_id = manual_id if manual_id is not None else unique_id

        with _lock:
            uid = GUID._build_uid(ns1, ns2, requested_id)

            attempts = 0
            max_attempts = 0xFFFF
            while uid in _uid_to_name_store:
                if requested_id is not None:
                    raise ValueError(
                        f"UID collision: {uid:08X} already exists and requested id was fixed"
                    )
                attempts += 1
                if attempts > max_attempts:
                    raise RuntimeError("Failed to generate unique ID after max attempts")
                uid = GUID._build_uid(ns1, ns2, None)

            GUID._register_name(uid, GUID._build_full_namespace(ns1, ns2, uid, name))
            if instance is not None:
                GUID._register_instance(uid, instance)

        return uid

    @staticmethod
    def add_name(uid: GUID, name: str) -> None:
        """Add or update the name associated with a UID. Thread-safe."""
        with _lock:
            if uid not in _uid_to_name_store:
                raise KeyError(f"Cannot add name to non-existent UID {uid:08X}")
            ns1, ns2, _unique_id = GUID._parse_uid(uid)
            full_name = GUID._build_full_namespace(ns1, ns2, uid, name)
            GUID._register_name(uid, full_name)

    @staticmethod
    def add_instance(uid: GUID, instance: object) -> None:
        """Add or update the instance associated with a UID. Thread-safe."""
        with _lock:
            if uid not in _uid_to_name_store:
                raise KeyError(f"Cannot add instance to non-existent UID {uid:08X}")
            GUID._register_instance(uid, instance)

    @staticmethod
    def remove(uid: GUID) -> bool:
        """Remove a UID from the store. Returns True if it existed, False otherwise.

        Thread-safe.
        """
        with _lock:
            name = _uid_to_name_store.pop(uid, None)
            if name is None:
                return False

            _name_to_uid_store.pop(name, None)

            instance = _uid_to_instance_store.pop(uid, None)
            if instance is not None:
                instance_id = id(instance)
                registered_uids = _instance_id_to_uids.get(instance_id)
                if registered_uids is not None:
                    _instance_id_to_uids[instance_id] = [
                        registered_uid
                        for registered_uid in registered_uids
                        if registered_uid != uid
                    ]
                    if not _instance_id_to_uids[instance_id]:
                        _instance_id_to_uids.pop(instance_id, None)

            return True

    @staticmethod
    def exists(uid: GUID) -> bool:
        """Check if a UID exists in the store. Thread-safe."""
        with _lock:
            return uid in _uid_to_name_store

    @staticmethod
    def clear() -> None:
        """Clear all stored UIDs. Useful for testing. Thread-safe."""
        with _lock:
            _uid_to_name_store.clear()
            _name_to_uid_store.clear()
            _uid_to_instance_store.clear()
            _instance_id_to_uids.clear()

    @property
    def parse(self) -> tuple[GUID.Entity, GUID.Owner, int]:
        """Parse a UID into its namespace components."""
        return GUID._parse_uid(self)

    def lookup_name(self, with_namespace: bool = False) -> str:
        """Return the registered name for this UID.

        If with_namespace is False, only the terminal name segment is returned.
        """
        with _lock:
            name = _uid_to_name_store.get(self)
        if name is None:
            return f"NotFound_{self:08X}"
        return name if with_namespace else name.split(".")[-1]

    def lookup_instance(self, with_namespace: bool = False) -> tuple[object | None, str | None]:
        """Return the registered instance and its associated name for this UID."""
        with _lock:
            instance = _uid_to_instance_store.get(self)
            name = _uid_to_name_store.get(self)
        if name is not None and not with_namespace:
            name = name.split(".")[-1]
        return instance, name

    @property
    def get_name(self) -> str:
        """Backward-compatible property returning the short name."""
        return self.lookup_name()

    @property
    def get_instance(self) -> tuple[object | None, str | None]:
        """Backward-compatible property returning the instance and short name."""
        return self.lookup_instance()

    @staticmethod
    def get_uid(name: str | object) -> GUID:
        """Retrieve the GUID associated with a full name or instance."""
        with _lock:
            if isinstance(name, str):
                uid = _name_to_uid_store.get(name)
                if uid is not None:
                    return uid
            else:
                registered_uids = _instance_id_to_uids.get(id(name), [])
                if registered_uids:
                    return registered_uids[0]
        raise KeyError(f"No GUID found for name {name}")


GUID.NameSpaces.Entity = GUID.Entity
GUID.NameSpaces.Owner = GUID.Owner
