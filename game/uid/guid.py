from __future__ import annotations

from uuid import UUID

from game.uid.guid import uuid4 as random_uuid

"""Utility functions for generating and handling Unique Identifiers (GUID) in the game.

Currently, this module provides a function to generate random UUID4 identifiers as a placeholder for future GUID implementations.
"""

def uuid4() -> UUID:
    """Generate a random UUID4."""
    return random_uuid()