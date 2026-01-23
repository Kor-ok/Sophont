from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import indent
from typing import Union, cast

from sortedcontainers import SortedKeyList

from game.characteristic import Characteristic
from game.gene import Gene
from game.package import AttributePackage
from game.phene import Phene
from game.species import Species

GeneOrPhene = Union[Gene, Phene]


class Acquired:
    __slots__ = ('package', 'age_acquired_seconds', 'context')

    def __init__(self, package: AttributePackage, age_acquired_seconds: int, context: int):
        self.package = package
        self.age_acquired_seconds = age_acquired_seconds
        self.context = context

    @classmethod
    def by_age(cls, package: AttributePackage, age_seconds: int, context: int) -> Acquired:
        return cls(package=package, context=context, age_acquired_seconds=age_seconds)
    
    def __repr__(self) -> str:
        return f"Acquired(package={repr(self.package)}, age_acquired_seconds={self.age_acquired_seconds}, context={repr(self.context)})"
def _package_key(acquired: Acquired) -> tuple[int, int]:
    return (acquired.package.item.characteristic.upp_index, acquired.age_acquired_seconds)


@dataclass
class UniqueAppliedCharacteristic:
    item: Characteristic
    computed_level: int
    training_progress: float = field(default=0.0)

UPPIndexAndLevel = tuple[int, int]
UniqueIDAndLevel = dict[bytes, UPPIndexAndLevel]
class Epigenetics:
    """
    characteristics_collation: list[UniqueAppliedCharacteristic] | None - Cached list of unique applied characteristics with computed levels.

    acquired_packages_collection: SortedKeyList[Acquired] ordered by (gene.characteristic.upp_index, age_acquired_seconds)
    is_packages_dirty: bool - Flag to indicate if the aptitude collation needs to be recomputed.
    parent_uuids: list[bytes] - List of parent UUIDs used for inheritance tracking.
    species: Species - The unique species identifier and GENOTYPE:genetic blueprint of the sophont.
    """
    __slots__ = (
        'characteristics_collation',
        'acquired_packages_collection', 
        'is_packages_dirty', 
        'parent_uuids',
        'gender',
        'species'
        )
    def __init__(self, species: Species):
        # === HOT DATA (frequently updated) ============================
        self.characteristics_collation: list[UniqueAppliedCharacteristic] | None = None

        # === WARM DATA (infrequently updated) ============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key)
        self.is_packages_dirty = False

        # === COLD DATA (rarely updated) ================================
        self.parent_uuids: list[int] = [] # First entry should always be self UUID for cloning scenarios.
        self.gender: tuple[int, int] = (-1, -1)  # -1 = unspecified where first=selected gender out of, second=max gene(non grafted) contributors

        # === NEVER UPDATED DATA === (But Frequently Read) ================
        self.species: Species = species

    def insert_package_acquired(self, package: AttributePackage, age_acquired_seconds: int, context: int, trigger_collation: bool = False) -> None:
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, context=context)
        self.acquired_packages_collection.add(acquired)
        self.is_packages_dirty = True
        if trigger_collation:
            self.update_collation()

    def remove_package_acquired(self, package: AttributePackage, age_acquired_seconds: int, context: int, trigger_collation: bool = False) -> None:
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, context=context)
        self.acquired_packages_collection.remove(acquired)
        self.is_packages_dirty = True
        if trigger_collation:
            self.update_collation()

    def get_acquired_packages(self) -> list[AttributePackage]:
        return [acquired.package for acquired in self.acquired_packages_collection]
    
    def auto_generate_inherited_packages(self) -> None:
        raise NotImplementedError()

    def update_collation(self) -> None:
        if not self.is_packages_dirty:
            return
        
        # An Acquired package is a AttributePackage whose item is a Gene or Phene.
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
        display.append(f"species={self.species!r}")
        display.append(f"parent_uuids=[{', '.join(repr(uuid) for uuid in self.parent_uuids)}]")
        display.append(f"gender={self.gender!r}")
        display.append(f"acquired_packages_collection=[{', '.join(repr(acq) for acq in self.acquired_packages_collection)}]")
        if self.characteristics_collation is None:
            display.append("characteristics_collation=None")
        else:
            display.append(f"characteristics_collation=[{', '.join(repr(char) for char in self.characteristics_collation)}]")
        # Join with Newlines for readability
        return "EpigeneticProfile(\n" + indent(",\n".join(display), indentation) + "\n)"