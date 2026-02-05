from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union, cast

from sortedcontainers import SortedKeyList

from components.primitives.data import FullCode
from sophont.acquisitions import Acquired
from systems.attributes.characteristic import Characteristic
from systems.attributes.gene import Gene
from systems.attributes.package import AttributePackage
from systems.attributes.phene import Phene
from systems.attributes.species import Species


def _package_key(acquired: Acquired) -> int:
    """Key function for SortedKeyList: order by age_acquired_seconds."""
    return acquired.age_acquired_seconds


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
    parent_guids: list[bytes] - List of parent GUIDs used for inheritance tracking.
    species: Species - The unique species identifier and GENOTYPE:genetic blueprint of the sophont.
    """

    __slots__ = (
        "characteristics_collation",
        "acquired_packages_collection",
        "is_packages_dirty",
        "parent_guids",
        "gender",
        "species",
    )

    species: Species

    def __init__(self, species: Species):
        # === HOT DATA (frequently updated) ============================
        self.characteristics_collation: list[UniqueAppliedCharacteristic] | None = None

        # === WARM DATA (infrequently updated) ============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key)
        self.is_packages_dirty = False

        # === COLD DATA (rarely updated) ================================
        self.parent_guids: list[int] = (
            []
        )  # First entry should always be self GUID for cloning scenarios.
        self.gender: tuple[int, int] = (
            -1,
            -1,
        )  # -1 = unspecified where first=selected gender out of, second=max gene(non grafted) contributors

        # === NEVER UPDATED DATA === (But Frequently Read) ================
        self.species: Species = species

    def insert_package_acquired(
        self,
        package: AttributePackage,
        age_acquired_seconds: int,
        context_guid: int,
        trigger_collation: bool = False,
    ) -> bool:
        """Insert an acquired package if not already present.

        Returns True if inserted, False if duplicate (same package+context_guid already exists).
        """
        acquired = Acquired.by_age(
            package=package, age_seconds=age_acquired_seconds, context_guid=context_guid
        )
        # Check for duplicate (same package+context_guid) before adding
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
        context_guid: int,
        trigger_collation: bool = False,
    ) -> bool:
        """Remove an acquired package if present.

        Returns True if removed, False if not found.
        Note: age_acquired_seconds is not used for matching (equality is by package+context_guid only).
        """
        acquired = Acquired.by_age(
            package=package, age_seconds=age_acquired_seconds, context_guid=context_guid
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

        # An Acquired package is a AttributePackage whose item is a Gene or Phene.
        # Both Gene and Phene have characteristic: Characteristic.
        # For each Acquired:
        # sum up all the package levels where the Characteristic matches so that we create
        # a UniqueAppliedCharacteristic for each unique Characteristic and apply the summed level
        # whilst preserving any training_progress from previous collation.

        previous_training_progress: dict[FullCode, float] = {}
        if self.characteristics_collation is not None:
            for characteristic in self.characteristics_collation:
                key: FullCode = (
                    characteristic.item.code[0],
                    characteristic.item.code[1],
                    characteristic.item.code[2],
                )
                previous_training_progress[key] = float(characteristic.training_progress)

        level_by_characteristic: dict[FullCode, int] = {}
        characteristic_by_key: dict[FullCode, Characteristic] = {}

        for acquired in self.acquired_packages_collection:
            package = acquired.package
            # Package items are Gene/Phene; we collate by their shared Characteristic.
            item = cast(Union[Gene, Phene], package.item)
            characteristic = item.characteristic
            key: FullCode = (
                characteristic.code[0],
                characteristic.code[1],
                characteristic.code[2],
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
                    training_progress=training_progress,
                )
            )

        self.characteristics_collation = sorted(
            collation,
            key=lambda a: (a.item.code[0], a.item.code[1], a.item.code[2]),
        )
        self.is_packages_dirty = False