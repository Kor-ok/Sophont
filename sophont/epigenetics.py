from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import indent
from typing import Union, cast

from sortedcontainers import SortedKeyList

from game.characteristic import Characteristic
from game.characteristic_package import CharacteristicPackage
from game.gene import Gene
from game.genotype import Genotype
from game.phene import Phene

GeneOrPhene = Union[Gene, Phene]


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


@dataclass
class UniqueAppliedCharacteristic:
    item: Characteristic
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
        if trigger_collation:
            self.update_collation()

    def get_acquired_packages(self) -> list[CharacteristicPackage]:
        return [acquired.package for acquired in self.acquired_packages_collection]
    
    def auto_generate_inherited_packages(self) -> None:
        raise NotImplementedError()

    def update_collation(self) -> None:
        if not self.is_packages_dirty:
            return
        
        # An Acquired package is a CharacteristicPackage whose item is a Gene or Phene.
        # Both Gene and Phene have characteristic: Characteristic.
        # For each Acquired: 
        # sum up all the package levels where the Characteristic matches so that we create
        # a UniqueAppliedCharacteristic for each unique Characteristic and apply the summed level
        # whilst preserving any training_progress from previous collation.

        previous_training_progress: dict[Characteristic.Key, float] = {}
        if self.characteristics_collation is not None:
            for characteristic in self.characteristics_collation:
                key: Characteristic.Key = (
                    characteristic.item.upp_index,
                    characteristic.item.subtype,
                    characteristic.item.category_code,
                )
                previous_training_progress[key] = float(characteristic.training_progress)

        level_by_characteristic: dict[Characteristic.Key, int] = {}
        characteristic_by_key: dict[Characteristic.Key, Characteristic] = {}

        for acquired in self.acquired_packages_collection:
            package = acquired.package
            # Package items are Gene/Phene; we collate by their shared Characteristic.
            item = cast(GeneOrPhene, package.item)
            characteristic = item.characteristic
            key: Characteristic.Key = (
                characteristic.upp_index,
                characteristic.subtype,
                characteristic.category_code,
            )

            level_by_characteristic[key] = level_by_characteristic.get(key, 0) + int(package.level)
            characteristic_by_key[key] = characteristic
            

        collation: list[UniqueAppliedCharacteristic] = []
        for key, computed_level in level_by_characteristic.items():
            characteristic = characteristic_by_key[key]
            training_progress = previous_training_progress.get(key, 0.0)

            collation.append(
                UniqueAppliedCharacteristic(
                    item=characteristic,
                    computed_level=computed_level,
                    training_progress=training_progress
                )
            )

        self.characteristics_collation = sorted(
            collation,
            key=lambda a: (a.item.upp_index, a.item.subtype, a.item.category_code),
        )
        self.is_packages_dirty = False

    
    def __repr__(self) -> str:
        indentation = "  "
        display = []
        display.append(f"genotype={self.genotype!r}")
        display.append(f"acquired_packages_collection=[{', '.join(repr(acq) for acq in self.acquired_packages_collection)}]")
        if self.characteristics_collation is None:
            display.append("characteristics_collation=None")
        else:
            display.append(f"characteristics_collation=[{', '.join(repr(char) for char in self.characteristics_collation)}]")
        # Join with Newlines for readability
        return "EpigeneticProfile(\n" + indent(",\n".join(display), indentation) + "\n)"