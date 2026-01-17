from __future__ import annotations

from uuid import UUID

from game.uid.guid import uuid4 as random_uuid
from game.uid.guid import uuid5 as namespace_uuid

"""Utility functions for generating and handling Unique Identifiers (GUID) in the game.

Currently, this module provides a function to generate random UUID4 identifiers as a placeholder for future GUID implementations.
"""

_NAMESPACE_MAP: dict[str, UUID] = {
    # Placeholder for future namespace UUIDs.
    # "example_namespace": UUID("12345678-1234-5678-1234-567812345678"),
}

class GUID:
    """Class representing a Global Unique Identifier (GUID) for game entities.

    This is a placeholder implementation that currently uses UUID4 for uniqueness.
    Future implementations may include additional features or formats.
    """
    __slots__ = ('uid',)

    def __init__(self, uid: bytes):
        self.uid = uid

    @classmethod
    def generate(cls, purpose: str | None = None) -> GUID:
        """Generate a uuid4 if purpose is None, else uuid5."""
        if purpose is not None:
            namespace = UUID("12345678-1234-5678-1234-567812345678")  # Example fixed namespace UUID
            return cls(uid=namespace_uuid(namespace, purpose).bytes)
        else:
            return cls(uid=random_uuid().bytes)

def uuid4() -> UUID:
    """Generate a random UUID4."""
    return random_uuid()

def uuid5(namespace: UUID, name: str) -> UUID:
    """Generate a UUID5 based on a namespace and name."""
    return namespace_uuid(namespace, name)