from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union, cast

from sortedcontainers import SortedKeyList

from game.knowledge import Knowledge
from game.mappings.data import FullCode
from game.package import AttributePackage
from game.skill import Skill


class Acquired:
    """Tracks when an AttributePackage was acquired.

    Equality is based on (package, context) - the same package in the same context
    is considered a duplicate regardless of when it was acquired.
    """
    __slots__ = ('package', 'age_acquired_seconds', 'context')

    package: AttributePackage

    def __init__(self, package: AttributePackage, age_acquired_seconds: int, context: int):
        self.package = package
        self.age_acquired_seconds = age_acquired_seconds
        self.context = context

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
    
    def __repr__(self) -> str:
        return f"Acquired(package={repr(self.package)}, age_acquired_seconds={self.age_acquired_seconds}, context={repr(self.context)})"
    
def _package_key(acquired: Acquired) -> tuple[int, int]:
    return (acquired.package.item.base_code, acquired.age_acquired_seconds)

AptitudeCategory = type[Union[Skill, Knowledge]]
AptitudeSingleton = Union[Skill, Knowledge]
@dataclass    
class UniqueAppliedAptitude:
    item_type: AptitudeCategory
    item: AptitudeSingleton
    computed_level: int
    training_progress: float = field(default=0.0)


ItemFullCodeAndLevel = tuple[FullCode, int]
UID = int
UIDAndLevel = dict[UID, ItemFullCodeAndLevel]
class Aptitudes:
    """
    Aptitude Collation acts as a summary layer that extracts all unique aptitude items
    from the packages acquired by the character and sums up their level modifiers into computed levels.

    Packages Collection holds all the acquired packages in a sorted list, ordered by item code and age acquired.

    IMPORTANT: Package, Skill, Knowledge are all immutable flyweight singletons, so we can rely on 
    their identity and hash stability. While Acquired is a mutable container, it does not affect the immutability
    of the underlying items. Similarly UniqueAppliedAptitude is a mutable summary object, but its item references remain immutable.
    """
    __slots__ = (
        'aptitude_collation',
        'acquired_packages_collection',
        'is_packages_dirty'
    )
    def __init__(self):
        # === HOT DATA (frequently updated) ============================
        self.aptitude_collation: list[UniqueAppliedAptitude] | None = None
        # === COLD DATA (rarely updated) ===============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key) # SortedKeyList maintains order on insert; no re-sorting step needed.
        self.is_packages_dirty: bool = False

    def insert_package_acquired(
            self, 
            package: AttributePackage, 
            age_acquired_seconds: int, 
            context: int, 
            trigger_collation: bool = False
            ) -> bool:
        """Insert an acquired package if not already present.

        Returns True if inserted, False if duplicate (same package+context already exists).
        """
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, context=context)
        # Check for duplicate (same package+context) before adding
        if acquired in self.acquired_packages_collection:
            return False
        self.acquired_packages_collection.add(acquired)
        self.is_packages_dirty = True
        if trigger_collation:
            self.update_collation()
        return True
    
    def remove_package_acquired(
        self,
        package: AttributePackage,
        age_acquired_seconds: int,
        context: int,
        trigger_collation: bool = False,
    ) -> bool:
        """Remove an acquired package if present.

        Returns True if removed, False if not found.
        Note: age_acquired_seconds is not used for matching (equality is by package+context only).
        """
        acquired = Acquired.by_age(
            package=package, age_seconds=age_acquired_seconds, context=context
        )
        try:
            self.acquired_packages_collection.remove(acquired)
        except ValueError:
            return False
        self.is_packages_dirty = True
        if trigger_collation:
            self.update_collation()
        return True
    
    def get_acquired_packages(self) -> list[AttributePackage]:
        return [acquired.package for acquired in self.acquired_packages_collection]
    
    def update_collation(self) -> None:
        if not self.is_packages_dirty:
            return
        
        # For each unique singleton aptitude item (e.g. Skill or Knowledge), 
        # sum up all the package levels where the package item match.

        previous_training_progress: dict[UID, float] = {}
        if self.aptitude_collation is not None:
            for aptitude in self.aptitude_collation:
                uid = getattr(aptitude.item.base_code, "context_id", None)
                if isinstance(uid, UID):
                    previous_training_progress[int(uid)] = float(aptitude.training_progress)

        level_by_uid: dict[UID, int] = {}
        item_by_uid: dict[UID, AptitudeSingleton] = {}
        item_type_by_uid: dict[UID, AptitudeCategory] = {}

        for acquired in self.acquired_packages_collection:
            package = acquired.package
            item = cast(AptitudeSingleton, package.item)
            uid = getattr(item, "context_id", None)
            if not isinstance(uid, UID):
                # Skills/Knowledges are expected to provide a stable unique_id.
                # If not, fall back to identity-hashable behavior.
                uid = int(id(item))
                
            uid_b = int(uid)
            level_by_uid[uid_b] = level_by_uid.get(uid_b, 0) + int(package.level)
            item_by_uid[uid_b] = item
            item_type_by_uid[uid_b] = cast(AptitudeCategory, type(item))

        collation: list[UniqueAppliedAptitude] = []
        for uid_b, computed_level in level_by_uid.items():
            item = item_by_uid[uid_b]
            item_type = item_type_by_uid[uid_b]
            training_progress = previous_training_progress.get(uid_b, 0.0)
            collation.append(
                UniqueAppliedAptitude(
                    item_type=item_type,
                    item=item,
                    computed_level=int(computed_level),
                    training_progress=float(training_progress),
                )
            )

        def _sort_key(a: UniqueAppliedAptitude) -> tuple[int, int, int, str]:
            if isinstance(a.item, Skill):
                return (0, a.item.base_code, 0, "")
            if isinstance(a.item, Knowledge):
                return (1, int(a.item.associated_skill), int(a.item.base_code), str(a.item.focus))
            # Should never happen, but keeps sorting total.
            return (2, 0, 0, "")

        self.aptitude_collation = sorted(collation, key=_sort_key)
        self.is_packages_dirty = False