from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from sortedcontainers import SortedKeyList

from game.personal_day import PersonalDay
from game.primitives.data import FullCode
from sophont.acquisitions import Acquired
from sophont.attributes.characteristic import Characteristic
from sophont.attributes.package import AttributePackage


def _package_key(acquired: Acquired) -> int:
    """Key function for SortedKeyList: order by age_acquired_seconds."""
    return acquired.age_acquired_seconds
@dataclass
class UniqueAppliedCharacteristic:
    item: Characteristic
    computed_level: int
    training_progress: float = field(default=0.0)
class Personals:
     
    __slots__ = (
        "attributes_collation",
        "personal_day",
        "acquired_packages_collection",
        "is_packages_dirty"
    )

    def __init__(self, personal_day_characteristic: Characteristic) -> None:
        # === HOT DATA (frequently updated) ============================
        self.attributes_collation: list[UniqueAppliedCharacteristic] | None = None
        self.personal_day: PersonalDay = PersonalDay(personal_day_characteristic)

        # === WARM DATA (infrequently updated) ============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key)
        self.is_packages_dirty = False

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
        if self.attributes_collation is not None:
            for characteristic in self.attributes_collation:
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
            item = cast(Characteristic, package.item)
            characteristic = item
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

        self.attributes_collation = sorted(
            collation,
            key=lambda a: (a.item.code[0], a.item.code[1], a.item.code[2]),
        )
        self.is_packages_dirty = False