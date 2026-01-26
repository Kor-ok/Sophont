from __future__ import annotations

import game.event as venture
from game.characteristic import Characteristic
from game.package import AttributePackage
from game.skill import Skill


def initialise_example_packages() -> None:
    """Initialise example packages for testing purposes."""
    # This function is a placeholder for package initialisation logic.

    example_skill_package = AttributePackage(
        item = Skill.by_name("vacc suit"),
        level = 2,
        context_id = 123456789
    )

    example_characteristic_package = AttributePackage(
        item = Characteristic.by_name("soc"),
        level = 3,
        context_id = 987654321
    )

homeworld_event = venture.Event(name="Example Homeworld Venture")

