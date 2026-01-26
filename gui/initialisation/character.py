from __future__ import annotations

from random import randint

from game.package import AttributePackage
from game.phene import Phene
from gui.initialisation.species import example_sophont_1


def initialise_example_data() -> None:
    """Initialise example data for testing purposes."""
    
    # INHERITED PACKAGES

    genes_dict = example_sophont_1.epigenetics.species.genotype.get_genes_without_phenes()

    inherited_packages = []

    for upp_index in genes_dict:
        package = AttributePackage(
            item=genes_dict[upp_index],
            level=randint(1, 6),
            context_id=example_sophont_1.epigenetics.parent_uuids[randint(1, 2)],
        )
        inherited_packages.append(package)


    # INHERITANCE APPLICATIONS

    for package in inherited_packages:
        example_sophont_1.epigenetics.insert_package_acquired(
            package=package,
            age_acquired_seconds=-1,
            context=package.context_id,
            trigger_collation=False,
        )

    # BIRTH PACKAGES

    birth_packages = []

    for package in inherited_packages:
        birth_package = AttributePackage(
            item=Phene.by_characteristic_code(package.item.get_code()),
            level=randint(1, 6),
            context_id=package.context_id,
        )
        birth_packages.append(birth_package)

    phenes_dict = example_sophont_1.epigenetics.species.genotype.get_phenes_without_genes()

    for upp_index in phenes_dict:
        birth_package = AttributePackage(
            item=phenes_dict[upp_index],
            level=randint(1, 6)+randint(1, 6),
            context_id=example_sophont_1.uuid,
        )
        birth_packages.append(birth_package)


    # BIRTH APPLICATIONS

    for package in birth_packages:
        example_sophont_1.epigenetics.insert_package_acquired(
            package=package,
            age_acquired_seconds=0,
            context=package.context_id,
            trigger_collation=False,
        )

    example_sophont_1.epigenetics.update_collation()