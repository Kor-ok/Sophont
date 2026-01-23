from __future__ import annotations

from enum import Enum
from random import randint

"""Utility functions for generating and handling 32-bit Unique Identifiers (GUID) in the game.
"""

GLOBAL_UID_STORE = set()
class NameSpaces:
    """Totalling 16 bits, defines the branching namespaces for GUID generation and lookup.
    """
    class Entity(Enum):
        """Of 8 bits, defines the first namespace for the GUID.
        """
        CHARACTERS = 0o0
        SPECIES = 0o1
        PACKAGES = 0o2
        EVENTS = 0o3

    class Owner(Enum):
        """Of 8 bits, defines the second namespace branching from the first for the GUID.
        """
        PLAYER = 0o0
        NPC = 0o1
        ENV = 0o2

class GUID:
    """Stateless utility class managing the creation of non-clashing Global Unique Identifiers (GUID) for game entities.

    Namespaces are 8-bits each. The last 16-bits are randomly generated.
    """
    @staticmethod
    def _check_store_clash(uid: int) -> bool:
        if uid in GLOBAL_UID_STORE:
            return True
        GLOBAL_UID_STORE.add(uid)
        return False
    
    @staticmethod
    def _constructor(ns1: NameSpaces.Entity, ns2: NameSpaces.Owner, unique_id: int | None = None) -> int:
        if unique_id is None:
            unique_id = randint(0, 0xFFFF)
        uid = (ns1.value << 24) | (ns2.value << 16) | unique_id
        return uid
    
    @staticmethod
    def generate(ns1: NameSpaces.Entity, ns2: NameSpaces.Owner, unique_id: int | None = None) -> int:

        uid = GUID._constructor(ns1, ns2, unique_id)

        while GUID._check_store_clash(uid):
            uid = GUID._constructor(ns1, ns2, unique_id)

        return uid
    
    @staticmethod
    def parse(uid: int) -> tuple[NameSpaces.Entity, NameSpaces.Owner, int]:
        ns1 = NameSpaces.Entity((uid >> 24) & 0xFF)
        ns2 = NameSpaces.Owner((uid >> 16) & 0xFF)
        unique_id = uid & 0xFFFF
        return ns1, ns2, unique_id