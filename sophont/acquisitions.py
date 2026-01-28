from __future__ import annotations

from game.package import AttributePackage


class Acquired:
    """Tracks when an AttributePackage was acquired and optionally applies expiration as part of temporary state management systems.

    Equality is based on (package, context) - the same package in the same context
    is considered a duplicate regardless of when it was acquired.
    """
    __slots__ = (
        'package', 
        'age_acquired_seconds', 
        'expires_at_seconds',
        'context'
        )

    package: AttributePackage

    def __init__(
            self, 
            package: AttributePackage, 
            age_acquired_seconds: int, 
            context: int,
            ):
        self.package = package
        self.age_acquired_seconds = age_acquired_seconds
        self.context = context
        # Compute expiry from package duration; callers should not supply this.
        expires_at_seconds: int | None = None
        if package.duration_seconds > 0 and self.age_acquired_seconds >= 0:
            expires_at_seconds = self.age_acquired_seconds + package.duration_seconds
        object.__setattr__(self, 'expires_at_seconds', expires_at_seconds)

    @classmethod
    def by_age(cls, package: AttributePackage, age_seconds: int, context: int) -> Acquired:
        return cls(package=package, context=context, age_acquired_seconds=age_seconds)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Acquired):
            return NotImplemented
        # Same package (flyweight identity) and same context means duplicate
        return self.package is other.package and self.context == other.context

    def __hash__(self) -> int:
        # Hash by package identity and context for set-like duplicate detection
        return hash((id(self.package), self.context))