from __future__ import annotations

from random import randint

from game.package import AttributePackage
from game.phene import Phene
from game.uid.guid import GUID, NameSpaces
from gui.initialisation.species import example_sophont_1


def initialise_example_data() -> None:
    """Initialise example data for testing purposes."""
    # example_sophont_1.epigenetics.update_collation()
    example_package_1 = AttributePackage(
        item=Phene.by_characteristic_name("Social"),
        level=1,
    )
    example_sophont_1.epigenetics.insert_package_acquired(
        package=example_package_1,
        age_acquired_seconds=-1,
        context=1,
        trigger_collation=True,
        )