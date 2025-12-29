from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Type, Union, Tuple, cast

from sortedcontainers import SortedKeyList

from game.aptitude_package import AptitudePackage
from game.skill import Skill
from game.knowledge import Knowledge

# Sophont > Aptitudes > [Acquired] > Package > Skill/Knowledge > Modifier Values
# Sophont > Aptitudes > [UniqueAppliedAptitude] > Of Package Type (i.e. Skill|Knowledge) > Sum of Modifier Values

class Acquired:
    __slots__ = ('package', 'age_acquired_seconds', 'memo')

    def __init__(self, package: AptitudePackage, age_acquired_seconds: int, memo: Optional[str] = None):
        object.__setattr__(self, 'package', package)
        object.__setattr__(self, 'age_acquired_seconds', age_acquired_seconds)
        object.__setattr__(self, 'memo', memo)

    @classmethod
    def by_age(cls, package: AptitudePackage, age_seconds: int, memo: Optional[str] = None) -> 'Acquired':
        return cls(package=package, memo=memo, age_acquired_seconds=age_seconds)
    
    def __repr__(self) -> str:
        return f"Acquired(package={repr(self.package)}, age_acquired_seconds={self.age_acquired_seconds}, memo={repr(self.memo)})"
    
def _package_key(acquired: Acquired) -> Tuple[int, int]:
    return (acquired.package.item.code, acquired.age_acquired_seconds)

AptitudeCategory = Type[Union[Skill, Knowledge]]
AptitudeSingleton = Union[Skill, Knowledge]
@dataclass    
class UniqueAppliedAptitude:
    item_type: AptitudeCategory
    item: AptitudeSingleton
    computed_level: int
    training_progress: float = field(default=0.0)


ItemCodeAndLevel = Tuple[int, int]
UniqueIDAndLevel = Dict[bytes, ItemCodeAndLevel]
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
        self.aptitude_collation: Optional[List[UniqueAppliedAptitude]] = None
        # === COLD DATA (rarely updated) ===============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key) # SortedKeyList maintains order on insert; no re-sorting step needed.
        self.is_packages_dirty: bool = False

    def insert_package_acquired(self, package: AptitudePackage, age_acquired_seconds: int, memo: Optional[str] = None, trigger_collation: bool = False) -> None:
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, memo=memo)
        self.acquired_packages_collection.add(acquired)
        self.is_packages_dirty = True
        if trigger_collation:
            self.update_collation()

    def update_collation(self) -> None:
        if not self.is_packages_dirty:
            return
        
        # For each unique singleton aptitude item (e.g. Skill or Knowledge), 
        # sum up all the package levels where the package item match.

        previous_training_progress: Dict[bytes, float] = {}
        if self.aptitude_collation is not None:
            for aptitude in self.aptitude_collation:
                uid = getattr(aptitude.item, "unique_id", None)
                if isinstance(uid, (bytes, bytearray)):
                    previous_training_progress[bytes(uid)] = float(aptitude.training_progress)

        level_by_uid: Dict[bytes, int] = {}
        item_by_uid: Dict[bytes, AptitudeSingleton] = {}
        item_type_by_uid: Dict[bytes, AptitudeCategory] = {}

        for acquired in self.acquired_packages_collection:
            package = acquired.package
            item = cast(AptitudeSingleton, package.item)
            uid = getattr(item, "unique_id", None)
            if not isinstance(uid, (bytes, bytearray)):
                # Skills/Knowledges are expected to provide a stable unique_id.
                # If not, fall back to identity-hashable behavior.
                uid = id(item).to_bytes(8, "little", signed=False)
            uid_b = bytes(uid)

            level_by_uid[uid_b] = level_by_uid.get(uid_b, 0) + int(package.level)
            item_by_uid[uid_b] = item
            item_type_by_uid[uid_b] = cast(AptitudeCategory, type(item))

        collation: List[UniqueAppliedAptitude] = []
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

        def _sort_key(a: UniqueAppliedAptitude) -> Tuple[int, int, int, str]:
            if isinstance(a.item, Skill):
                return (0, a.item.code, 0, "")
            if isinstance(a.item, Knowledge):
                return (1, int(a.item.associated_skill), int(a.item.code), str(a.item.focus))
            # Should never happen, but keeps sorting total.
            return (2, 0, 0, "")

        self.aptitude_collation = sorted(collation, key=_sort_key)
        self.is_packages_dirty = False