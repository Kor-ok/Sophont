from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import indent
from typing import cast

from sortedcontainers import SortedKeyList

from game.characteristic import Characteristic
from game.package import AttributePackage
from game.personal_day import PersonalDay
from sophont.acquisitions import Acquired


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
        context: int,
        trigger_collation: bool = False,
    ) -> bool:
        """Insert an acquired package if not already present.

        Returns True if inserted, False if duplicate (same package+context already exists).
        """
        acquired = Acquired.by_age(
            package=package, age_seconds=age_acquired_seconds, context=context
        )
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

        # An Acquired package is a AttributePackage whose item is a Gene or Phene.
        # Both Gene and Phene have characteristic: Characteristic.
        # For each Acquired:
        # sum up all the package levels where the Characteristic matches so that we create
        # a UniqueAppliedCharacteristic for each unique Characteristic and apply the summed level
        # whilst preserving any training_progress from previous collation.

        previous_training_progress: dict[Characteristic.Key, float] = {}
        if self.attributes_collation is not None:
            for characteristic in self.attributes_collation:
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
            item = cast(Characteristic, package.item)
            characteristic = item
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
                    training_progress=training_progress,
                )
            )

        self.attributes_collation = sorted(
            collation,
            key=lambda a: (a.item.upp_index, a.item.subtype, a.item.category_code),
        )
        self.is_packages_dirty = False

        def __repr__(self) -> str:
            indentation = "  "
            display = []
            display.append(
                f"acquired_packages_collection=[{', '.join(repr(acq) for acq in self.acquired_packages_collection)}]"
            )
            if self.attributes_collation is None:
                display.append("attributes_collation=None")
            else:
                display.append(
                    f"attributes_collation=[{', '.join(repr(char) for char in self.attributes_collation)}]"
                )
            # Join with Newlines for readability
            return "Personals(\n" + indent(",\n".join(display), indentation) + "\n)"