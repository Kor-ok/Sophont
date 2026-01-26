from __future__ import annotations

from random import randint

from game.mappings.set import ATTRIBUTES
from game.package import AttributePackage
from game.phene import Phene
from game.skill import Skill
from gui.initialisation.species import example_sophont_1


def initialise_example_data() -> None:
    """Initialise example data for testing purposes."""
    
    # INHERITED PACKAGES ==============================

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

    # DEFAULT, PERSONALS, INTUITIONS BIRTH APTITUDES ==============================
        # Skills of sub category 1, 3, 4 where sub category is:
        # SecondaryCodeInt in FullCode of AliasMappedFullCode from all_skills
    criteria = {
        1: set([1, 3, 4])
    }
    filtered_skills = ATTRIBUTES.skills.combined_collection.get_filtered_collection(criteria=criteria)

    skill_packages = []
    for entry in filtered_skills:
        skill_instance = Skill.by_code(entry[1])
        skill_package = AttributePackage(
            item=skill_instance,
            level=0,
            context_id=example_sophont_1.uuid,
        )
        skill_packages.append(skill_package)

    # SKILLS AT BIRTH APPLICATIONS
    for package in skill_packages:
        example_sophont_1.aptitudes.insert_package_acquired(
            package=package,
            age_acquired_seconds=0,
            context=package.context_id,
            trigger_collation=False,
        )

    example_life_skill_package = AttributePackage(
        item = Skill.by_code(ATTRIBUTES.skills.get_full_code("vacc suit")),
        level = 2,
        context_id = 123456789
    )
    example_sophont_1.aptitudes.insert_package_acquired(
        package=example_life_skill_package,
        age_acquired_seconds=31556952 * 18,
        context=example_life_skill_package.context_id,
        trigger_collation=False,
    )

    example_sophont_1.aptitudes.update_collation()