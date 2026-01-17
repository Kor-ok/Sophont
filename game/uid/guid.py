from __future__ import annotations

from uuid import UUID

from game.uid.guid import uuid4 as random_uuid

"""Utility functions for generating and handling Unique Identifiers (GUID) in the game.

Currently, this module provides a function to generate random UUID4 identifiers as a placeholder for future GUID implementations.
"""

class GUID:
    """Class representing a Global Unique Identifier (GUID) for game entities.

    This is a placeholder implementation that currently uses UUID4 for uniqueness.
    Future implementations may include additional features or formats.
    """
    __slots__ = ('uid',)

    def __init__(self, uid: bytes):
        self.uid = uid

    @classmethod
    def generate(cls) -> GUID:
        """Generate a new random GUID."""
        return cls(uid=random_uuid().bytes)

def uuid4() -> UUID:
    """Generate a random UUID4."""
    return random_uuid()