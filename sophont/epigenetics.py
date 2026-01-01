from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union, cast

from sortedcontainers import SortedKeyList

from game.characteristic_package import CharacteristicPackage
from game.gene import Gene
from game.genotype import Genotype
from game.phene import Phene


class Acquired:
    __slots__ = ('package', 'age_acquired_seconds', 'memo')

    def __init__(self, package: CharacteristicPackage, age_acquired_seconds: int, memo: list[str] | None = None):
        self.package = package
        self.age_acquired_seconds = age_acquired_seconds
        self.memo = memo

    @classmethod
    def by_age(cls, package: CharacteristicPackage, age_seconds: int, memo: list[str] | None = None) -> Acquired:
        return cls(package=package, memo=memo, age_acquired_seconds=age_seconds)
    
    def __repr__(self) -> str:
        return f"Acquired(package={repr(self.package)}, age_acquired_seconds={self.age_acquired_seconds}, memo={repr(self.memo)})"

def _package_key(acquired: Acquired) -> tuple[int, int]:
    return (acquired.package.item.characteristic.upp_index, acquired.age_acquired_seconds)

CharacteristicCategory = type[Union[Gene, Phene]]
CharacteristicSingleton = Union[Gene, Phene]
@dataclass
class UniqueAppliedCharacteristic:
    item_type: CharacteristicCategory
    item: CharacteristicSingleton
    computed_level: int
    training_progress: float = field(default=0.0)

UPPIndexAndLevel = tuple[int, int]
UniqueIDAndLevel = dict[bytes, UPPIndexAndLevel]
class EpigeneticProfile:
    """
    characteristics_collation: list[UniqueAppliedCharacteristic] | None - Cached list of unique applied characteristics with computed levels.

    acquired_packages_collection: SortedKeyList[Acquired] ordered by (gene.characteristic.upp_index, age_acquired_seconds)
    is_packages_dirty: bool - Flag to indicate if the aptitude collation needs to be recomputed.
    genotype: SpeciesGenotype - The genetic blueprint of the sophont.
    """
    __slots__ = (
        'characteristics_collation',
        'acquired_packages_collection', 
        'is_packages_dirty', 
        'genotype'
        )
    def __init__(self, genotype: Genotype):
        # === HOT DATA (frequently updated) ============================
        self.characteristics_collation: list[UniqueAppliedCharacteristic] | None = None

        # === COLD DATA (infrequently updated) ============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key)
        self.is_packages_dirty = False

        # === NEVER UPDATED DATA === (But Frequently Read) ================
        self.genotype = genotype

    def insert_package_acquired(self, package: CharacteristicPackage, age_acquired_seconds: int, memo: list[str] | None = None, trigger_collation: bool = False) -> None:
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, memo=memo)
        self.acquired_packages_collection.add(acquired)
        self.is_packages_dirty = True

    def update_collation(self) -> None:
        if not self.is_packages_dirty:
            return
        
        # For each unique singleton characteristic item (e.g. Gene or Phene), 
        # sum up all the package levels where the package item match.

        previous_training_progress: dict[bytes, float] = {}
        if self.characteristics_collation is not None:
            for characteristic in self.characteristics_collation:
                uid = getattr(characteristic.item, "unique_id", None)
                if isinstance(uid, (bytes, bytearray)):
                    previous_training_progress[bytes(uid)] = float(characteristic.training_progress)

        level_by_uid: dict[bytes, int] = {}
        item_by_uid: dict[bytes, CharacteristicSingleton] = {}
        item_type_by_uid: dict[bytes, CharacteristicCategory] = {}

        for acquired in self.acquired_packages_collection:
            package = acquired.package
            item = cast(CharacteristicSingleton, package.item)
            uid = getattr(item, "unique_id", None)
            if not isinstance(uid, (bytes, bytearray)):
                # Genes/Phenes are expected to provide a stable unique_id.
                # If not, fall back to identity-hashable behavior.
                uid = id(item).to_bytes(8, "little", signed=False)
            uid_b = bytes(uid)

            level_by_uid[uid_b] = level_by_uid.get(uid_b, 0) + int(package.level)
            item_by_uid[uid_b] = item
            item_type_by_uid[uid_b] = cast(CharacteristicCategory, type(item))

        collation: list[UniqueAppliedCharacteristic] = []
        for uid_b, computed_level in level_by_uid.items():
            item = item_by_uid[uid_b]
            item_type = item_type_by_uid[uid_b]
            training_progress = previous_training_progress.get(uid_b, 0.0)

            collation.append(
                UniqueAppliedCharacteristic(
                    item_type=item_type,
                    item=item,
                    computed_level=computed_level,
                    training_progress=training_progress
                )
            )

            def _sort_key(a: UniqueAppliedCharacteristic) -> tuple[int, int, int, str]:
                if isinstance(a.item, Gene):
                    return (0, a.item.characteristic.upp_index, 0, "")
                if isinstance(a.item, Phene):
                    return (1, a.item.characteristic.upp_index, 0, "")
                
                return (2, 0, 0, "")
            
            self.characteristics_collation = sorted(collation, key=_sort_key)
            self.is_packages_dirty = False


                
        
